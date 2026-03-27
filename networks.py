import torch
import torch.nn as nn
import torch.nn.functional as F

def weights_init_(m):
    if isinstance(m, nn.Linear):
        nn.init.orthogonal_(m.weight.data)
        if m.bias is not None:
            m.bias.data.fill_(0.0)

class LocalActor(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super(LocalActor, self).__init__()
        self.l1 = nn.Linear(state_dim, hidden_dim)
        self.l2 = nn.Linear(hidden_dim, hidden_dim)
        self.l3 = nn.Linear(hidden_dim, hidden_dim)
        
        self.mean_layer = nn.Linear(hidden_dim, action_dim)
        self.log_std_layer = nn.Linear(hidden_dim, action_dim)
        
        self.apply(weights_init_)

    def forward(self, state):
        x = F.relu(self.l1(state))
        x = F.relu(self.l2(x))
        x = F.relu(self.l3(x))
        
        mean = self.mean_layer(x)
        log_std = self.log_std_layer(x)
        log_std = torch.clamp(log_std, -20, 2)
        return mean, log_std

    def sample(self, state):
        mean, log_std = self.forward(state)
        # 额外健壮性：防止上游出现 NaN 直接导致 Normal 抛错并中断训练
        mean = torch.nan_to_num(mean, nan=0.0, posinf=0.0, neginf=0.0)
        log_std = torch.nan_to_num(log_std, nan=-20.0, posinf=2.0, neginf=-20.0)
        std = log_std.exp().clamp(min=1e-6, max=1e2)
        normal = torch.distributions.Normal(mean, std)
        x_t = normal.rsample()
        action = torch.tanh(x_t)
        
        log_prob = normal.log_prob(x_t)
        log_prob -= torch.log(1 - action.pow(2) + 1e-6)
        log_prob = log_prob.sum(1, keepdim=True)
        return action, log_prob

class LocalCritic(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super(LocalCritic, self).__init__()
        self.l1 = nn.Linear(state_dim + action_dim, hidden_dim)
        self.l2 = nn.Linear(hidden_dim, hidden_dim)
        self.l3 = nn.Linear(hidden_dim, hidden_dim)
        
        self.c_head = nn.Linear(hidden_dim, 1)
        self.e_head = nn.Linear(hidden_dim, 1)
        self.apply(weights_init_)

    def forward(self, state, action):
        x = torch.cat([state, action], 1)
        x = F.relu(self.l1(x))
        x = F.relu(self.l2(x))
        x = F.relu(self.l3(x))
        return self.c_head(x), self.e_head(x)

class GlobalMixer(nn.Module):
    def __init__(self, num_agents, hidden_dim=64):
        super(GlobalMixer, self).__init__()
        self.l1 = nn.Linear(num_agents, hidden_dim)
        self.l2 = nn.Linear(hidden_dim, hidden_dim)
        self.head = nn.Linear(hidden_dim, 1)
        self.apply(weights_init_)

    def forward(self, c_values):
        x = F.relu(self.l1(c_values))
        x = F.relu(self.l2(x))
        return self.head(x)