import torch
import torch.nn as nn
import torch.nn.functional as F


def weights_init_(m):
    if isinstance(m, nn.Linear):
        nn.init.orthogonal_(m.weight.data)
        if m.bias is not None:
            m.bias.data.fill_(0.0)


# Reuse Actor/Critic definitions
from networks import LocalActor, LocalCritic  # noqa: F401


class GraphAttentionLayer(nn.Module):
    """Graph Attention Layer (GAT) with **weighted adjacency** support.

    Notes:
        - `adj` is interpreted as an edge-weight matrix (>=0). 0 means no edge.
        - We use masking via adj>0, then after softmax reweight by adj and renormalize.
        - This keeps attention normalized and lets stronger electrical coupling have larger influence.
    """

    def __init__(self, in_features, out_features, dropout=0.0, alpha=0.2, concat=True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.dropout = float(dropout)
        self.alpha = alpha
        self.concat = concat

        self.W = nn.Parameter(torch.empty(size=(in_features, out_features)))
        nn.init.xavier_uniform_(self.W.data, gain=1.414)

        self.a = nn.Parameter(torch.empty(size=(2 * out_features, 1)))
        nn.init.xavier_uniform_(self.a.data, gain=1.414)

        self.leakyrelu = nn.LeakyReLU(self.alpha)

    def forward(self, h, adj):
        # h: [B, N, Fin], adj: [N, N]
        B, N, _ = h.size()
        Wh = torch.matmul(h, self.W)  # [B, N, Fout]

        # Build pairwise concatenation for attention logits
        Wh_i = Wh.repeat(1, 1, N).view(B, N * N, -1)
        Wh_j = Wh.repeat(1, N, 1)
        a_input = torch.cat([Wh_i, Wh_j], dim=2).view(B, N, N, 2 * self.out_features)

        e = self.leakyrelu(torch.matmul(a_input, self.a).squeeze(3))  # [B, N, N]

        # Mask non-edges
        # adj can be [N,N] (shared) or [B,N,N] (per-sample)
        if adj.dim() == 2:
            adjw = adj.unsqueeze(0).expand_as(e)  # [B,N,N]
        elif adj.dim() == 3:
            if adj.size(0) != B:
                raise ValueError(f"adj batch dim mismatch: got {adj.size(0)} expected {B}")
            adjw = adj
        else:
            raise ValueError(f"adj must be [N,N] or [B,N,N], got {tuple(adj.shape)}")
        zero_vec = -9e15 * torch.ones_like(e)
        attention = torch.where(adjw > 0, e, zero_vec)

        attention = F.softmax(attention, dim=2)

        # Reweight by edge strength and renormalize
        attention = attention * adjw
        attention = attention / (attention.sum(dim=2, keepdim=True) + 1e-8)

        if self.dropout > 0:
            attention = F.dropout(attention, self.dropout, training=self.training)

        h_prime = torch.matmul(attention, Wh)  # [B, N, Fout]

        if self.concat:
            return F.elu(h_prime)
        else:
            return h_prime


class GraphMixer(nn.Module):
    """Topology-aware mixer for FMASAC.

    Design goals:
        1) Never underperform baseline MLP at initialization:
            - GAT head is zero-initialized
            - gate is initialized near 0 (sigmoid(-5) ~ 0.0067 (configurable))
        2) Stabilize SAC bootstrapping:
            - dropout default 0
            - residual + LayerNorm in the GAT stack
        3) Reduce small-graph permutation invariance issues:
            - agent ID embedding concatenated to node feature

    Forward:
        q = q_mlp + gate(c_values) * q_gat
    """

    def __init__(
        self,
        num_agents,
        adj_matrix,
        hidden_dim=64,
        id_dim=8,
        node_feat_dim: int = 0,
        dropout=0.0,
        alpha=0.2,
        ctx_dim: int = 0,
        edge_drop: float = 0.0,
        gate_init_bias: float = -5.0,
        gat_scale_init: float = 1.0,
    ):
        super().__init__()
        self.num_agents = int(num_agents)
        self.register_buffer('adj', adj_matrix.float())
        # Scale factor for the GAT branch (can be scheduled during training)
        self.register_buffer('gat_scale', torch.tensor(float(gat_scale_init), dtype=torch.float32))

        # Extra node feature dims for the GAT branch (derived from observations)
        self.node_feat_dim = int(node_feat_dim)
        self.edge_drop = float(edge_drop)

        self.id_dim = int(id_dim)
        self.agent_emb = nn.Embedding(self.num_agents, self.id_dim)

        # --- GAT branch ---
        gat_in = 1 + self.id_dim + self.node_feat_dim
        self.gat1 = GraphAttentionLayer(gat_in, hidden_dim, dropout=dropout, alpha=alpha, concat=True)
        self.gat2 = GraphAttentionLayer(hidden_dim, hidden_dim, dropout=dropout, alpha=alpha, concat=False)
        self.ln1 = nn.LayerNorm(hidden_dim)
        self.ln2 = nn.LayerNorm(hidden_dim)
        self.head_gat = nn.Linear(hidden_dim, 1)

        # --- MLP branch ---
        self.mlp_l1 = nn.Linear(self.num_agents, hidden_dim)
        self.mlp_l2 = nn.Linear(hidden_dim, hidden_dim)
        self.head_mlp = nn.Linear(hidden_dim, 1)

        # --- Gate ---
        self.gate = nn.Sequential(
            nn.Linear(self.num_agents, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

        # init
        self.apply(weights_init_)

        # Critical: start close to MLP-only
        nn.init.zeros_(self.head_gat.weight)
        nn.init.zeros_(self.head_gat.bias)

        nn.init.zeros_(self.gate[-1].weight)
        with torch.no_grad():
            self.gate[-1].bias.fill_(float(gate_init_bias))

        # --- Context branch (optional) ---
        self.ctx_dim = int(ctx_dim)
        if self.ctx_dim > 0:
            self.ctx_mlp = nn.Sequential(
                nn.Linear(self.ctx_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, 1),
            )
        else:
            self.ctx_mlp = None

    def set_adjacency(self, adj_matrix: torch.Tensor) -> None:
        """Update the stored adjacency matrix (e.g., after topology change)."""
        if adj_matrix is None:
            return
        with torch.no_grad():
            if adj_matrix.device != self.adj.device:
                adj_matrix = adj_matrix.to(self.adj.device)
            if tuple(adj_matrix.shape) != tuple(self.adj.shape):
                raise ValueError(f"adj shape mismatch: got {tuple(adj_matrix.shape)} expected {tuple(self.adj.shape)}")
            self.adj.copy_(adj_matrix.float())

    def set_gat_scale(self, scale: float) -> None:
        """Set a multiplicative scale for the GAT branch output.

        This is useful for warmup/ramp schedules where you start from an MLP-only
        mixer (scale=0) and gradually allow the topology-aware branch to
        contribute (scale -> 1).
        """
        with torch.no_grad():
            self.gat_scale.fill_(float(scale))

    def _drop_edge(self, adj: torch.Tensor) -> torch.Tensor:
        """DropEdge on the adjacency matrix during training.

        We drop off-diagonal edges with probability `edge_drop` and keep self-loops.
        For symmetry, we sample a mask on the upper triangle and mirror it.
        """
        if (not self.training) or self.edge_drop <= 0:
            return adj
        if adj.dim() != 2:
            return adj
        N = adj.size(0)
        if N <= 1:
            return adj

        # Binary edge existence mask (excluding diagonal)
        with torch.no_grad():
            m = (adj > 0).float()
            eye = torch.eye(N, device=adj.device, dtype=adj.dtype)
            m = m * (1.0 - eye)
            # sample mask on upper triangle only
            iu = torch.triu_indices(N, N, offset=1, device=adj.device)
            keep = torch.ones((iu.size(1),), device=adj.device, dtype=adj.dtype)
            drop = torch.rand_like(keep) < self.edge_drop
            keep = keep * (~drop).float()
            new_m = torch.zeros_like(adj)
            new_m[iu[0], iu[1]] = keep
            new_m = new_m + new_m.transpose(0, 1)
            # apply to existing edges only
            new_m = new_m * m
            # keep self-loops
            new_m = new_m + eye
        return adj * new_m

    def forward(self, c_values, ctx=None, node_feat: torch.Tensor | None = None):
        # c_values: [B, N]
        B, N = c_values.shape

        # optional node features: [B, N, F]
        if self.node_feat_dim > 0:
            if node_feat is None:
                node_feat = torch.zeros((B, N, self.node_feat_dim), device=c_values.device, dtype=c_values.dtype)
            else:
                if node_feat.dim() != 3 or node_feat.size(0) != B or node_feat.size(1) != N:
                    raise ValueError(f"node_feat shape must be [B,N,F], got {tuple(node_feat.shape)}")
                if node_feat.size(2) != self.node_feat_dim:
                    raise ValueError(f"node_feat last dim must be {self.node_feat_dim}, got {node_feat.size(2)}")

        # --- GAT path ---
        ids = torch.arange(N, device=c_values.device)
        id_feat = self.agent_emb(ids).unsqueeze(0).expand(B, -1, -1)  # [B,N,id_dim]

        if self.node_feat_dim > 0:
            x_g = torch.cat([c_values.unsqueeze(-1), id_feat, node_feat], dim=-1)  # [B,N,1+id+F]
        else:
            x_g = torch.cat([c_values.unsqueeze(-1), id_feat], dim=-1)  # [B,N,1+id]

        adj_use = self._drop_edge(self.adj)
        h1 = self.gat1(x_g, adj_use)  # [B,N,H]
        h1 = self.ln1(h1)
        h2 = self.gat2(h1, adj_use)  # [B,N,H]

        h = torch.relu(h2 + h1)
        h = self.ln2(h)

        q_gat = self.head_gat(h.mean(dim=1))  # [B,1]

        # --- MLP path ---
        x_m = F.relu(self.mlp_l1(c_values))
        x_m = F.relu(self.mlp_l2(x_m))
        q_mlp = self.head_mlp(x_m)

        gate = torch.sigmoid(self.gate(c_values))
        q = q_mlp + gate * self.gat_scale * q_gat
        if self.ctx_mlp is not None and ctx is not None:
            q = q + self.ctx_mlp(ctx)
        return q

    def param_groups(self, base_lr: float, gnn_lr_scale: float = 0.3, gate_lr_scale: float = 0.3, weight_decay: float = 0.0):
        """Return optimizer param groups to stabilize GNN training.

        - MLP branch: base_lr
        - GAT branch (+ agent_emb): base_lr * gnn_lr_scale
        - gate branch: base_lr * gate_lr_scale
        """
        mlp_params = list(self.mlp_l1.parameters()) + list(self.mlp_l2.parameters()) + list(self.head_mlp.parameters())
        gat_params = (
            list(self.agent_emb.parameters())
            + list(self.gat1.parameters())
            + list(self.gat2.parameters())
            + list(self.ln1.parameters())
            + list(self.ln2.parameters())
            + list(self.head_gat.parameters())
        )
        gate_params = list(self.gate.parameters())
        groups = [
            {"params": mlp_params, "lr": float(base_lr), "weight_decay": 0.0},
            {"params": gat_params, "lr": float(base_lr) * float(gnn_lr_scale), "weight_decay": float(weight_decay)},
            {"params": gate_params, "lr": float(base_lr) * float(gate_lr_scale), "weight_decay": 0.0},
        ]
        if self.ctx_mlp is not None:
            groups.append({"params": list(self.ctx_mlp.parameters()), "lr": float(base_lr), "weight_decay": 0.0})
        return groups
