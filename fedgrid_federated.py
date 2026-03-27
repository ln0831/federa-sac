from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence

import math
import numpy as np
import torch
import torch.nn.functional as F


def _to_tensor(x: Any, device: str | torch.device = 'cpu') -> torch.Tensor:
    if isinstance(x, torch.Tensor):
        return x.detach().to(device=device, dtype=torch.float32)
    return torch.as_tensor(x, dtype=torch.float32, device=device)


def row_normalize_weights(w: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    w = torch.nan_to_num(w, nan=0.0, posinf=0.0, neginf=0.0)
    w = torch.clamp(w, min=0.0)
    s = w.sum(dim=1, keepdim=True)
    return w / (s + eps)


def safe_cosine_matrix(x: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    x = torch.nan_to_num(x.float(), nan=0.0, posinf=0.0, neginf=0.0)
    x = x.view(x.shape[0], -1)
    denom = x.norm(dim=1, keepdim=True).clamp_min(eps)
    x = x / denom
    sim = x @ x.transpose(0, 1)
    sim = torch.clamp(sim, -1.0, 1.0)
    return 0.5 * (sim + 1.0)


def extract_obs_features(obs_list: Sequence[Any], clip_val: float = 5.0) -> torch.Tensor:
    feats = []
    for o in obs_list:
        t = _to_tensor(o, device='cpu').view(-1)
        d = int(t.numel())
        nbus = max(1, d // 3)
        p = t[:nbus]
        q = t[nbus:2 * nbus]
        v = t[2 * nbus:3 * nbus]
        f = torch.stack([
            p.mean(),
            q.mean(),
            v.abs().mean(),
            v.min(),
            v.max(),
            p.std(unbiased=False) if p.numel() > 1 else torch.zeros((), dtype=torch.float32),
            q.std(unbiased=False) if q.numel() > 1 else torch.zeros((), dtype=torch.float32),
            v.std(unbiased=False) if v.numel() > 1 else torch.zeros((), dtype=torch.float32),
        ])
        if clip_val is not None and clip_val > 0:
            f = torch.clamp(f, -clip_val, clip_val)
        feats.append(f)
    return torch.stack(feats, dim=0)


def reduce_embedding_list(embeddings: Sequence[Any], clip_val: float = 10.0) -> torch.Tensor:
    feats = []
    for z in embeddings:
        t = _to_tensor(z, device='cpu')
        if t.dim() == 0:
            t = t.view(1)
        elif t.dim() >= 2:
            t = t.mean(dim=0)
        t = t.view(-1)
        if clip_val is not None and clip_val > 0:
            t = torch.clamp(t, -clip_val, clip_val)
        feats.append(t)
    if not feats:
        raise ValueError('embeddings cannot be empty')
    max_dim = max(int(t.numel()) for t in feats)
    feats = [torch.nn.functional.pad(t, (0, max(0, max_dim - int(t.numel())))) for t in feats]
    return torch.stack(feats, dim=0)


@dataclass
class FederatedStats:
    weight_entropy: float
    proto_sim_mean: float
    topo_sim_mean: float
    trust_mean: float
    trust_min: float
    trust_max: float
    stale_mean: float

    def to_dict(self) -> Dict[str, float]:
        return {
            'weight_entropy': float(self.weight_entropy),
            'proto_sim_mean': float(self.proto_sim_mean),
            'topo_sim_mean': float(self.topo_sim_mean),
            'trust_mean': float(self.trust_mean),
            'trust_min': float(self.trust_min),
            'trust_max': float(self.trust_max),
            'stale_mean': float(self.stale_mean),
        }


class AgentPrototypeBank:
    def __init__(self, num_agents: int, feature_dim: int = 8, momentum: float = 0.95):
        self.num_agents = int(num_agents)
        self.feature_dim = int(feature_dim)
        self.momentum = float(momentum)
        self.prototypes = torch.zeros(self.num_agents, self.feature_dim, dtype=torch.float32)
        self.reward_ema = torch.zeros(self.num_agents, dtype=torch.float32)
        self.count = 0

    def update_from_obs_list(self, obs_list: Sequence[Any]) -> None:
        self.update_from_tensor_matrix(extract_obs_features(obs_list))

    def update_from_tensor_matrix(self, feats: torch.Tensor) -> None:
        feats = _to_tensor(feats, device='cpu')
        if feats.shape != self.prototypes.shape:
            self.feature_dim = int(feats.shape[1])
            self.prototypes = torch.zeros_like(feats)
        if self.count == 0:
            self.prototypes = feats.clone()
        else:
            m = float(self.momentum)
            self.prototypes = m * self.prototypes + (1.0 - m) * feats
        self.count += 1

    def update_rewards(self, rewards: Sequence[float], momentum: float = 0.97) -> None:
        r = _to_tensor(rewards, device='cpu').view(-1)
        if r.numel() != self.num_agents:
            return
        if self.count <= 1:
            self.reward_ema = r.clone()
        else:
            m = float(momentum)
            self.reward_ema = m * self.reward_ema + (1.0 - m) * r

    def prototype_similarity(self) -> torch.Tensor:
        if self.count == 0:
            return torch.eye(self.num_agents, dtype=torch.float32)
        return safe_cosine_matrix(self.prototypes)

    def mean_drift(self) -> float:
        if self.count <= 1:
            return 0.0
        center = self.prototypes.mean(dim=0, keepdim=True)
        return float((self.prototypes - center).norm(dim=1).mean().item())


class HybridPrototypeBank:
    def __init__(
        self,
        num_agents: int,
        obs_feature_dim: int = 8,
        gnn_feature_dim: int = 32,
        momentum: float = 0.95,
        obs_weight: float = 0.35,
        gnn_weight: float = 0.65,
    ):
        self.num_agents = int(num_agents)
        self.momentum = float(momentum)
        self.obs_weight = float(obs_weight)
        self.gnn_weight = float(gnn_weight)
        self.obs_bank = AgentPrototypeBank(num_agents=num_agents, feature_dim=obs_feature_dim, momentum=momentum)
        self.gnn_dim = int(max(1, gnn_feature_dim))
        self.gnn_prototypes = torch.zeros(self.num_agents, self.gnn_dim, dtype=torch.float32)
        self.gnn_count = 0
        self.reward_ema = torch.zeros(self.num_agents, dtype=torch.float32)

    @property
    def count(self) -> int:
        return max(int(self.obs_bank.count), int(self.gnn_count))

    def update_from_obs_list(self, obs_list: Sequence[Any]) -> None:
        self.obs_bank.update_from_obs_list(obs_list)

    def update_from_embeddings(self, embeddings: Sequence[Any]) -> None:
        feats = reduce_embedding_list(embeddings)
        if feats.shape[0] != self.num_agents:
            return
        if self.gnn_prototypes.shape != feats.shape:
            self.gnn_dim = int(feats.shape[1])
            self.gnn_prototypes = torch.zeros_like(feats)
        if self.gnn_count == 0:
            self.gnn_prototypes = feats.clone()
        else:
            m = float(self.momentum)
            self.gnn_prototypes = m * self.gnn_prototypes + (1.0 - m) * feats
        self.gnn_count += 1

    def update_rewards(self, rewards: Sequence[float], momentum: float = 0.97) -> None:
        self.obs_bank.update_rewards(rewards, momentum=momentum)
        self.reward_ema = self.obs_bank.reward_ema.clone()

    def prototype_similarity(self) -> torch.Tensor:
        parts = []
        weights = []
        if self.obs_weight > 0.0 and self.obs_bank.count > 0:
            parts.append(self.obs_bank.prototype_similarity())
            weights.append(self.obs_weight)
        if self.gnn_weight > 0.0 and self.gnn_count > 0:
            parts.append(safe_cosine_matrix(self.gnn_prototypes))
            weights.append(self.gnn_weight)
        if not parts:
            return torch.eye(self.num_agents, dtype=torch.float32)
        out = torch.zeros_like(parts[0])
        for w, p in zip(weights, parts):
            out = out + float(w) * p
        return row_normalize_weights(out / max(1e-8, float(sum(weights))))

    def mean_drift(self) -> float:
        vals = []
        weights = []
        if self.obs_bank.count > 1 and self.obs_weight > 0:
            vals.append(self.obs_bank.mean_drift())
            weights.append(self.obs_weight)
        if self.gnn_count > 1 and self.gnn_weight > 0:
            center = self.gnn_prototypes.mean(dim=0, keepdim=True)
            vals.append(float((self.gnn_prototypes - center).norm(dim=1).mean().item()))
            weights.append(self.gnn_weight)
        if not vals:
            return 0.0
        return float(sum(v * w for v, w in zip(vals, weights)) / max(1e-8, sum(weights)))


def _should_keep_key(key: str, exclude_prefixes: Sequence[str], exclude_keys: Sequence[str]) -> bool:
    if key in set(exclude_keys):
        return False
    for p in exclude_prefixes:
        if key.startswith(p):
            return False
    return True


def flatten_module_signature(
    module: torch.nn.Module,
    *,
    exclude_prefixes: Sequence[str] = (),
    exclude_keys: Sequence[str] = (),
    max_params: int = 200000,
) -> torch.Tensor:
    chunks = []
    used = 0
    for key, value in module.state_dict().items():
        if not torch.is_tensor(value):
            continue
        if not torch.is_floating_point(value):
            continue
        if not _should_keep_key(key, exclude_prefixes, exclude_keys):
            continue
        flat = value.detach().float().view(-1).cpu()
        if flat.numel() == 0:
            continue
        remaining = max(0, int(max_params) - used)
        if remaining <= 0:
            break
        if flat.numel() > remaining:
            flat = flat[:remaining]
        chunks.append(flat)
        used += int(flat.numel())
    if not chunks:
        return torch.zeros(1, dtype=torch.float32)
    return torch.cat(chunks, dim=0)


def trust_scores_from_modules(
    modules: Sequence[torch.nn.Module],
    *,
    reward_ema: Optional[torch.Tensor] = None,
    exclude_prefixes: Sequence[str] = (),
    exclude_keys: Sequence[str] = (),
    temperature: float = 4.0,
) -> torch.Tensor:
    sigs = [flatten_module_signature(m, exclude_prefixes=exclude_prefixes, exclude_keys=exclude_keys) for m in modules]
    L = max(int(s.numel()) for s in sigs)
    mat = torch.stack([torch.nn.functional.pad(s, (0, max(0, L - int(s.numel())))) for s in sigs], dim=0)
    centroid = mat.mean(dim=0, keepdim=True)
    sims = torch.nn.functional.cosine_similarity(mat, centroid, dim=1).clamp(-1.0, 1.0)
    sims = 0.5 * (sims + 1.0)
    if reward_ema is not None and reward_ema.numel() == sims.numel():
        r = reward_ema.detach().float().cpu()
        r = (r - r.mean()) / (r.std(unbiased=False) + 1e-6)
        r = torch.sigmoid(r)
        sims = 0.7 * sims + 0.3 * r
    temp = max(1e-3, float(temperature))
    trust = torch.softmax(temp * sims, dim=0) * float(len(modules))
    return trust.clamp(min=0.05)


def sample_active_clients(num_agents: int, dropout_rate: float, *, rng: Optional[np.random.RandomState] = None) -> torch.Tensor:
    n = int(num_agents)
    p = float(np.clip(dropout_rate, 0.0, 0.95))
    if p <= 0.0:
        return torch.ones(n, dtype=torch.bool)
    rng = rng if rng is not None else np.random.RandomState()
    mask = rng.rand(n) >= p
    if not mask.any():
        mask[int(rng.randint(0, n))] = True
    return torch.as_tensor(mask, dtype=torch.bool)


def apply_participation_mask(weight_matrix: torch.Tensor, active_mask: torch.Tensor, *, freeze_inactive: bool = True) -> torch.Tensor:
    W = _to_tensor(weight_matrix, device='cpu').clone()
    active = _to_tensor(active_mask, device='cpu').view(-1) > 0.5
    n = int(W.shape[0])
    if active.numel() != n:
        raise ValueError(f'active_mask shape {tuple(active.shape)} incompatible with n={n}')
    W[:, ~active] = 0.0
    W = row_normalize_weights(W)
    if freeze_inactive:
        eye = torch.eye(n, dtype=W.dtype)
        W[~active] = eye[~active]
    return row_normalize_weights(W)


def select_byzantine_clients(active_mask: torch.Tensor, frac: float, *, rng: Optional[np.random.RandomState] = None) -> list[int]:
    active = np.flatnonzero(_to_tensor(active_mask, device='cpu').numpy() > 0.5)
    if active.size == 0:
        return []
    frac = float(np.clip(frac, 0.0, 1.0))
    if frac <= 0.0:
        return []
    k = int(math.floor(frac * float(active.size)))
    if k <= 0:
        return []
    rng = rng if rng is not None else np.random.RandomState()
    chosen = rng.choice(active, size=k, replace=False)
    return [int(x) for x in chosen.tolist()]


def _iter_named_float_tensors(module: torch.nn.Module):
    for name, param in module.named_parameters(recurse=True):
        if torch.is_floating_point(param.data):
            yield name, param.data
    for name, buf in module.named_buffers(recurse=True):
        if torch.is_floating_point(buf.data):
            yield name, buf.data


@torch.no_grad()
def inject_module_perturbation(
    modules: Sequence[torch.nn.Module],
    client_ids: Sequence[int],
    *,
    mode: str = 'noise',
    strength: float = 0.5,
    exclude_prefixes: Sequence[str] = (),
    exclude_keys: Sequence[str] = (),
    seed: Optional[int] = None,
) -> None:
    mode = str(mode or 'noise').lower()
    strength = float(max(0.0, strength))
    if mode in {'none', ''} or strength <= 0.0:
        return
    gen = torch.Generator(device='cpu')
    if seed is not None:
        gen.manual_seed(int(seed))
    for cid in client_ids:
        if cid < 0 or cid >= len(modules):
            continue
        m = modules[int(cid)]
        for name, tensor in _iter_named_float_tensors(m):
            if not _should_keep_key(name, exclude_prefixes, exclude_keys):
                continue
            if tensor.numel() == 0:
                continue
            if mode == 'noise':
                scale = float(tensor.detach().float().std().item()) if tensor.numel() > 1 else 1.0
                scale = max(scale, 1e-3)
                tensor.add_(torch.randn(tensor.shape, generator=gen, device=tensor.device, dtype=tensor.dtype) * (strength * scale))
            elif mode == 'signflip':
                tensor.mul_(-max(1.0, strength))
            elif mode == 'scale':
                tensor.mul_(1.0 + strength)
            else:
                raise ValueError(f'Unsupported byzantine mode: {mode}')


def build_federated_weight_matrix(
    *,
    topology_w: torch.Tensor,
    prototype_bank: Optional[AgentPrototypeBank | HybridPrototypeBank],
    actor_modules: Sequence[torch.nn.Module],
    critic_modules: Optional[Sequence[torch.nn.Module]] = None,
    mode: str = 'topo_proto',
    reward_ema: Optional[torch.Tensor] = None,
    staleness: Optional[torch.Tensor] = None,
    topo_weight: float = 0.45,
    proto_weight: float = 0.35,
    trust_weight: float = 0.20,
    stale_weight: float = 0.10,
    trust_temperature: float = 4.0,
    active_mask: Optional[torch.Tensor] = None,
    consensus_eta: float = 0.50,
) -> tuple[torch.Tensor, Dict[str, Any]]:
    mode = str(mode or 'topo_proto').lower()
    topo = row_normalize_weights(_to_tensor(topology_w, device='cpu'))
    n = int(topo.shape[0])

    if prototype_bank is not None and getattr(prototype_bank, 'count', 0) > 0:
        proto = prototype_bank.prototype_similarity().cpu()
    else:
        proto = torch.eye(n, dtype=torch.float32)
    proto = row_normalize_weights(proto)

    trust_a = trust_scores_from_modules(
        actor_modules,
        reward_ema=reward_ema,
        exclude_prefixes=('l1.', 'mean_layer.', 'log_std_layer.'),
        temperature=trust_temperature,
    )
    if critic_modules is not None:
        trust_c = trust_scores_from_modules(
            critic_modules,
            reward_ema=reward_ema,
            exclude_prefixes=('l1.', 'c_head.', 'e_head.'),
            temperature=trust_temperature,
        )
        trust = 0.5 * (trust_a + trust_c)
    else:
        trust = trust_a

    if staleness is None:
        stale_gate = torch.ones(n, dtype=torch.float32)
        stale_mean = 0.0
    else:
        s = _to_tensor(staleness, device='cpu').view(-1)
        if s.numel() != n:
            s = torch.zeros(n, dtype=torch.float32)
        stale_gate = torch.exp(-float(stale_weight) * s)
        stale_mean = float(s.mean().item())

    if mode == 'fedavg':
        W = torch.ones_like(topo)
    elif mode == 'topo':
        W = topo.clone()
    elif mode == 'proto':
        W = proto.clone()
    else:
        tw = max(0.0, float(topo_weight))
        pw = max(0.0, float(proto_weight))
        denom = max(1e-6, tw + pw)
        base = (tw * topo + pw * proto) / denom
        column_gate = (1.0 - float(trust_weight)) + float(trust_weight) * trust.view(1, -1)
        column_gate = column_gate * stale_gate.view(1, -1)
        W = base * column_gate
        if mode == 'consensus':
            W = 0.5 * (W + W.transpose(0, 1))
            eta = float(np.clip(consensus_eta, 0.0, 1.0))
            W = (1.0 - eta) * W + eta * torch.eye(n, dtype=W.dtype)

    W = row_normalize_weights(W)
    if active_mask is not None:
        W = apply_participation_mask(W, active_mask, freeze_inactive=True)

    entropy = float((-(W * (W.clamp_min(1e-8)).log()).sum(dim=1)).mean().item())
    stats = FederatedStats(
        weight_entropy=entropy,
        proto_sim_mean=float(proto.mean().item()),
        topo_sim_mean=float(topo.mean().item()),
        trust_mean=float(trust.mean().item()),
        trust_min=float(trust.min().item()),
        trust_max=float(trust.max().item()),
        stale_mean=float(stale_mean),
    ).to_dict()
    stats['trust_vector'] = trust
    stats['stale_gate'] = stale_gate
    stats['proto_drift'] = float(prototype_bank.mean_drift()) if prototype_bank is not None else 0.0
    if active_mask is not None:
        stats['active_frac'] = float((_to_tensor(active_mask, 'cpu') > 0.5).float().mean().item())
    return W, stats


def adaptive_parameter_mix(
    modules: Sequence[torch.nn.Module],
    weight_matrix: torch.Tensor,
    *,
    alpha: float = 1.0,
    exclude_prefixes: Sequence[str] = (),
    exclude_keys: Sequence[str] = (),
    strict: bool = False,
    source_gate: Optional[torch.Tensor] = None,
    active_mask: Optional[torch.Tensor] = None,
    update_clip: float = 0.0,
    trim_ratio: float = 0.0,
    attack_indices: Sequence[int] = (),
    attack_mode: str = 'none',
    attack_scale: float = 1.0,
    generator: Optional[torch.Generator] = None,
) -> None:
    if modules is None or len(modules) <= 1:
        return

    W = _to_tensor(weight_matrix, device='cpu')
    n = len(modules)
    if W.shape != (n, n):
        raise ValueError(f'weight_matrix shape {tuple(W.shape)} != ({n}, {n})')

    if active_mask is not None:
        W = apply_participation_mask(W, active_mask, freeze_inactive=True)

    if source_gate is not None:
        sg = _to_tensor(source_gate, device='cpu').view(1, -1)
        if sg.numel() == n:
            W = W * sg

    if trim_ratio > 0.0:
        sg = W.mean(dim=0)
        k = max(1, int(math.ceil((1.0 - float(trim_ratio)) * n)))
        keep_idx = torch.topk(sg, k=k, largest=True).indices
        mask = torch.zeros_like(sg)
        mask[keep_idx] = 1.0
        W = W * mask.view(1, -1)

    W = row_normalize_weights(W)
    state_dicts = [m.state_dict() for m in modules]
    keys = list(state_dicts[0].keys())
    new_state_dicts = [{k: (v.clone() if torch.is_tensor(v) else v) for k, v in sd.items()} for sd in state_dicts]

    def attack_tensor(t: torch.Tensor, idx: int) -> torch.Tensor:
        if idx not in set(int(i) for i in attack_indices):
            return t
        mode = str(attack_mode or 'none').lower()
        if mode in {'none', '', 'off'}:
            return t
        if mode == 'signflip':
            return -max(1.0, float(attack_scale)) * t
        if mode == 'gaussian':
            sigma = float(t.detach().float().std().item()) if t.numel() > 1 else 1.0
            sigma = max(sigma, 1e-3)
            noise = torch.randn(t.shape, generator=generator, device=t.device, dtype=t.dtype) * (float(attack_scale) * sigma)
            return t + noise
        if mode == 'zero':
            return torch.zeros_like(t)
        return t

    for k in keys:
        if not _should_keep_key(k, exclude_prefixes, exclude_keys):
            continue
        if not all(torch.is_tensor(sd[k]) for sd in state_dicts):
            continue
        if not torch.is_floating_point(state_dicts[0][k]):
            continue
        shapes = [tuple(sd[k].shape) for sd in state_dicts]
        if not all(s == shapes[0] for s in shapes):
            continue

        stacked = torch.stack([attack_tensor(sd[k].float().cpu(), i) for i, sd in enumerate(state_dicts)], dim=0)
        mixed = torch.einsum('ij,j...->i...', W, stacked)
        for i in range(n):
            src = state_dicts[i][k].float().cpu()
            tgt = mixed[i]
            if float(alpha) != 1.0:
                tgt = (1.0 - float(alpha)) * src + float(alpha) * tgt
            if float(update_clip) > 0.0:
                upd = tgt - src
                src_norm = src.norm().clamp_min(1e-8)
                max_norm = float(update_clip) * float(src_norm.item())
                upd_norm = float(upd.norm().item())
                if upd_norm > max_norm > 0.0:
                    upd = upd * (max_norm / (upd_norm + 1e-8))
                    tgt = src + upd
            new_state_dicts[i][k] = tgt.to(dtype=state_dicts[i][k].dtype)

    for i, m in enumerate(modules):
        m.load_state_dict(new_state_dicts[i], strict=bool(strict))



def estimate_module_payload_bits(
    modules: Sequence[torch.nn.Module],
    *,
    exclude_prefixes: Sequence[str] = (),
    exclude_keys: Sequence[str] = (),
    bits_per_param: int = 32,
) -> int:
    total = 0
    for m in modules or ():
        for name, tensor in _iter_named_float_tensors(m):
            if not _should_keep_key(name, exclude_prefixes, exclude_keys):
                continue
            total += int(tensor.numel()) * int(bits_per_param)
    return int(total)


def _merge_smallest_cluster(assign: list[int], affinity: torch.Tensor) -> list[int]:
    ids = sorted(set(int(x) for x in assign))
    if len(ids) <= 1:
        return assign
    members = {cid: [i for i, c in enumerate(assign) if int(c) == cid] for cid in ids}
    smallest = min(ids, key=lambda cid: (len(members[cid]), cid))
    src = members[smallest]
    best_target = None
    best_score = -1.0
    for cid in ids:
        if cid == smallest:
            continue
        dst = members[cid]
        if not src or not dst:
            continue
        score = float(affinity[src][:, dst].mean().item())
        if score > best_score:
            best_score = score
            best_target = cid
    if best_target is None:
        best_target = ids[0] if ids[0] != smallest else ids[-1]
    out = list(assign)
    for i, c in enumerate(out):
        if int(c) == smallest:
            out[i] = int(best_target)
    uniq = {cid: idx for idx, cid in enumerate(sorted(set(int(x) for x in out)))}
    return [uniq[int(c)] for c in out]


def derive_client_clusters(
    affinity: torch.Tensor,
    *,
    knn: int = 2,
    threshold: float = 0.58,
    max_clusters: int = 4,
    active_mask: Optional[torch.Tensor] = None,
) -> list[int]:
    A = _to_tensor(affinity, device='cpu')
    n = int(A.shape[0])
    A = 0.5 * (A + A.transpose(0, 1))
    A.fill_diagonal_(1.0)

    if active_mask is None:
        active = torch.ones(n, dtype=torch.bool)
    else:
        active = _to_tensor(active_mask, device='cpu').view(-1) > 0.5
        if active.numel() != n:
            active = torch.ones(n, dtype=torch.bool)

    graph = {i: set() for i in range(n)}
    thr = float(np.clip(threshold, 0.0, 1.0))
    k = max(1, min(int(knn), max(1, n - 1)))

    active_ids = [i for i in range(n) if bool(active[i])]
    for i in active_ids:
        vals = A[i].clone()
        vals[i] = -1.0
        topk = torch.topk(vals, k=k, largest=True).indices.tolist() if n > 1 else []
        for j in topk:
            if j == i or not bool(active[j]):
                continue
            if float(A[i, j].item()) >= thr:
                graph[i].add(int(j))
                graph[j].add(int(i))

    comp_assign = [-1] * n
    next_cid = 0
    for i in range(n):
        if comp_assign[i] != -1:
            continue
        if not bool(active[i]):
            comp_assign[i] = next_cid
            next_cid += 1
            continue
        stack = [i]
        comp_assign[i] = next_cid
        while stack:
            u = stack.pop()
            for v in graph[u]:
                if comp_assign[v] == -1:
                    comp_assign[v] = next_cid
                    stack.append(v)
        next_cid += 1

    uniq = sorted(set(int(c) for c in comp_assign))
    remap = {cid: idx for idx, cid in enumerate(uniq)}
    comp_assign = [remap[int(c)] for c in comp_assign]

    while len(set(comp_assign)) > max(1, int(max_clusters)):
        comp_assign = _merge_smallest_cluster(comp_assign, A)

    return [int(c) for c in comp_assign]


def mask_weights_by_clusters(
    weight_matrix: torch.Tensor,
    cluster_ids: Sequence[int],
    *,
    inter_cluster_scale: float = 0.05,
    self_boost: float = 0.0,
) -> torch.Tensor:
    W = _to_tensor(weight_matrix, device='cpu').clone()
    n = int(W.shape[0])
    clusters = [int(c) for c in cluster_ids]
    if len(clusters) != n:
        raise ValueError(f'cluster_ids length {len(clusters)} incompatible with n={n}')
    inter = float(np.clip(inter_cluster_scale, 0.0, 1.0))
    mask = torch.full_like(W, inter)
    for i in range(n):
        for j in range(n):
            if clusters[i] == clusters[j]:
                mask[i, j] = 1.0
    W = W * mask
    if float(self_boost) > 0.0:
        W = W + float(self_boost) * torch.eye(n, dtype=W.dtype)
    return row_normalize_weights(W)


def distill_actors_from_peers(
    actors: Sequence[torch.nn.Module],
    actor_optims: Sequence[torch.optim.Optimizer],
    anchor_obs: Sequence[torch.Tensor],
    weight_matrix: torch.Tensor,
    *,
    coef: float = 0.0,
    steps: int = 1,
    log_std_weight: float = 0.25,
    grad_clip: float = 0.0,
    active_mask: Optional[torch.Tensor] = None,
    cluster_ids: Optional[Sequence[int]] = None,
    same_cluster_only: bool = False,
    source_gate: Optional[torch.Tensor] = None,
    excluded_teacher_ids: Sequence[int] = (),
) -> float:
    if actors is None or len(actors) <= 1:
        return 0.0
    if float(coef) <= 0.0 or int(steps) <= 0:
        return 0.0
    n = len(actors)
    if len(anchor_obs) != n or len(actor_optims) != n:
        return 0.0

    device = anchor_obs[0].device
    W = _to_tensor(weight_matrix, device=device)
    if W.shape != (n, n):
        return 0.0

    if active_mask is not None:
        active = (_to_tensor(active_mask, device=device).view(-1) > 0.5)
        if active.numel() != n:
            active = torch.ones(n, dtype=torch.bool, device=device)
    else:
        active = torch.ones(n, dtype=torch.bool, device=device)

    if cluster_ids is not None and same_cluster_only:
        W = mask_weights_by_clusters(W.cpu(), cluster_ids, inter_cluster_scale=0.0, self_boost=0.0).to(device)

    if source_gate is not None:
        sg = _to_tensor(source_gate, device=device).view(1, -1)
        if sg.numel() == n:
            W = W * sg

    for idx in excluded_teacher_ids:
        if 0 <= int(idx) < n:
            W[:, int(idx)] = 0.0

    for i in range(n):
        if not bool(active[i]):
            W[i] = 0.0
            W[i, i] = 1.0
            continue
        peer_mass = float((W[i].sum() - W[i, i]).item())
        if peer_mass > 1e-8:
            W[i, i] = 0.0
    W = row_normalize_weights(W)
    total_loss = 0.0
    counted = 0

    for _ in range(int(steps)):
        with torch.no_grad():
            teacher_stats = []
            for obs, actor in zip(anchor_obs, actors):
                mu, ls = actor(obs)
                teacher_stats.append((mu.detach(), ls.detach()))

        for i in range(n):
            if not bool(active[i]):
                continue
            target_mu_shape = tuple(teacher_stats[i][0].shape)
            target_ls_shape = tuple(teacher_stats[i][1].shape)
            compatible_ids = [
                j for j in range(n)
                if float(W[i, j].item()) > 0.0
                and tuple(teacher_stats[j][0].shape) == target_mu_shape
                and tuple(teacher_stats[j][1].shape) == target_ls_shape
            ]
            if not compatible_ids:
                continue
            weights = W[i, compatible_ids]
            if float(weights.sum().item()) <= 0.0:
                continue
            weights = (weights / weights.sum()).view(len(compatible_ids), 1, 1)
            teacher_mu = torch.stack([teacher_stats[j][0] for j in compatible_ids], dim=0)
            teacher_ls = torch.stack([teacher_stats[j][1] for j in compatible_ids], dim=0)
            teacher_mu = (weights * teacher_mu).sum(dim=0)
            teacher_ls = (weights * teacher_ls).sum(dim=0)

            mu, ls = actors[i](anchor_obs[i])
            loss = float(coef) * (
                F.mse_loss(mu, teacher_mu) + float(log_std_weight) * F.mse_loss(ls, teacher_ls)
            )
            actor_optims[i].zero_grad()
            loss.backward()
            if float(grad_clip) > 0.0:
                torch.nn.utils.clip_grad_norm_(actors[i].parameters(), float(grad_clip))
            actor_optims[i].step()
            total_loss += float(loss.item())
            counted += 1

    return float(total_loss / max(1, counted))
