import numpy as np
import torch


class MultiAgentReplayBuffer:
    """Multi-agent replay buffer with optional global context storage.

    Args:
        max_size: maximum transitions
        num_agents: number of agents
        obs_dims: list of per-agent observation dims
        act_dims: list of per-agent action dims
        ctx_dim: optional global context dim (0 disables)
    """

    def __init__(self, max_size, num_agents, obs_dims, act_dims, ctx_dim: int = 0):
        self.max_size = int(max_size)
        self.ptr = 0
        self.size = 0
        self.num_agents = int(num_agents)
        self.ctx_dim = int(ctx_dim)

        self.obs = [np.zeros((self.max_size, int(d)), dtype=np.float32) for d in obs_dims]
        self.acts = [np.zeros((self.max_size, int(d)), dtype=np.float32) for d in act_dims]
        self.next_obs = [np.zeros((self.max_size, int(d)), dtype=np.float32) for d in obs_dims]
        self.rews = np.zeros((self.max_size, self.num_agents), dtype=np.float32)
        self.dones = np.zeros((self.max_size, 1), dtype=np.float32)

        if self.ctx_dim > 0:
            self.ctx = np.zeros((self.max_size, self.ctx_dim), dtype=np.float32)
            self.next_ctx = np.zeros((self.max_size, self.ctx_dim), dtype=np.float32)
        else:
            self.ctx = None
            self.next_ctx = None

    def add(self, obs_list, act_list, rew_list, next_obs_list, done, ctx=None, next_ctx=None):
        for i in range(self.num_agents):
            self.obs[i][self.ptr] = obs_list[i]
            self.acts[i][self.ptr] = act_list[i]
            self.next_obs[i][self.ptr] = next_obs_list[i]

        self.rews[self.ptr] = np.array(rew_list, dtype=np.float32)
        self.dones[self.ptr] = float(done)

        if self.ctx_dim > 0:
            if ctx is None:
                ctx = np.zeros((self.ctx_dim,), dtype=np.float32)
            if next_ctx is None:
                next_ctx = np.zeros((self.ctx_dim,), dtype=np.float32)
            self.ctx[self.ptr] = np.asarray(ctx, dtype=np.float32)
            self.next_ctx[self.ptr] = np.asarray(next_ctx, dtype=np.float32)

        self.ptr = (self.ptr + 1) % self.max_size
        self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size):
        ind = np.random.randint(0, self.size, size=int(batch_size))

        obs_batch = [torch.FloatTensor(self.obs[i][ind]) for i in range(self.num_agents)]
        act_batch = [torch.FloatTensor(self.acts[i][ind]) for i in range(self.num_agents)]
        rew_batch = torch.FloatTensor(self.rews[ind])
        next_obs_batch = [torch.FloatTensor(self.next_obs[i][ind]) for i in range(self.num_agents)]
        done_batch = torch.FloatTensor(self.dones[ind])

        if self.ctx_dim > 0:
            ctx_batch = torch.FloatTensor(self.ctx[ind])
            next_ctx_batch = torch.FloatTensor(self.next_ctx[ind])
            return obs_batch, act_batch, rew_batch, next_obs_batch, done_batch, ctx_batch, next_ctx_batch

        return obs_batch, act_batch, rew_batch, next_obs_batch, done_batch


def soft_update(target, source, tau):
    for target_param, param in zip(target.parameters(), source.parameters()):
        target_param.data.copy_(target_param.data * (1.0 - tau) + param.data * tau)


def hard_update(target, source):
    for target_param, param in zip(target.parameters(), source.parameters()):
        target_param.data.copy_(param.data)


def _row_normalize_weights(w: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    """Row-normalize a nonnegative weight matrix."""
    w = torch.nan_to_num(w, nan=0.0, posinf=0.0, neginf=0.0)
    w = torch.clamp(w, min=0.0)
    s = w.sum(dim=1, keepdim=True)
    return w / (s + eps)


def topology_weighted_mix(
    modules,
    weight_matrix,
    alpha: float = 1.0,
    exclude_prefixes=(),
    exclude_keys=(),
    strict: bool = False,
):
    """Mix parameters of per-agent modules using a (row-normalized) topology weight matrix.

    This is a simple Graph-FL / topology-weighted FedAvg operator:

        theta_i <- (1-alpha)*theta_i + alpha*sum_j W_ij * theta_j

    Notes:
    - Only mixes *floating* tensors.
    - Skips keys whose tensor shapes differ across agents.
    - You can exclude keys by prefix or exact match.
    """
    if modules is None or len(modules) <= 1:
        return

    device = None
    # build W
    if isinstance(weight_matrix, torch.Tensor):
        W = weight_matrix.detach().float().clone()
    else:
        W = torch.tensor(weight_matrix, dtype=torch.float32)

    W = _row_normalize_weights(W)
    n = len(modules)
    if W.shape != (n, n):
        raise ValueError(f"weight_matrix shape {tuple(W.shape)} != ({n},{n})")

    # snapshot state dicts
    sds = [m.state_dict() for m in modules]
    keys = list(sds[0].keys())
    new_sds = [{k: v.clone() if torch.is_tensor(v) else v for k, v in sd.items()} for sd in sds]

    def _excluded(k: str) -> bool:
        for p in exclude_prefixes:
            if k.startswith(p):
                return True
        return k in set(exclude_keys)

    for k in keys:
        if _excluded(k):
            continue
        # all tensors? same shape?
        if not all(torch.is_tensor(sd[k]) for sd in sds):
            continue
        shapes = [tuple(sd[k].shape) for sd in sds]
        if not all(s == shapes[0] for s in shapes):
            continue
        if not torch.is_floating_point(sds[0][k]):
            continue

        stacked = torch.stack([sd[k].float() for sd in sds], dim=0)  # [N, ...]
        mixed = torch.einsum('ij,j...->i...', W, stacked)
        for i in range(n):
            src = sds[i][k]
            tgt = mixed[i].to(dtype=src.dtype)
            if float(alpha) != 1.0:
                new_sds[i][k] = (1.0 - float(alpha)) * src + float(alpha) * tgt
            else:
                new_sds[i][k] = tgt

    for i, m in enumerate(modules):
        m.load_state_dict(new_sds[i], strict=bool(strict))


def reset_optimizers_state(optims):
    """Clear Adam/RMSprop momentum states after an aggregation step."""
    if optims is None:
        return
    for opt in optims:
        try:
            opt.state.clear()
        except Exception:
            pass
