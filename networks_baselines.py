import torch
import torch.nn as nn
import torch.nn.functional as F

def weights_init_(m):
    if isinstance(m, nn.Linear):
        nn.init.orthogonal_(m.weight.data)
        if m.bias is not None:
            m.bias.data.fill_(0.0)

class CentralizedCritic(nn.Module):
    def __init__(self, total_obs_dim, total_act_dim, hidden_dim=256):
        super(CentralizedCritic, self).__init__()
        # 输入是所有 Agent 的 obs 和 act 拼接
        self.l1 = nn.Linear(total_obs_dim + total_act_dim, hidden_dim)
        self.l2 = nn.Linear(hidden_dim, hidden_dim)
        self.l3 = nn.Linear(hidden_dim, hidden_dim)
        
        # 输出全局 Q 值 (1维)
        self.q_head = nn.Linear(hidden_dim, 1)
        self.apply(weights_init_)

    def forward(self, all_obs, all_acts):
        x = torch.cat([all_obs, all_acts], dim=1)
        x = F.relu(self.l1(x))
        x = F.relu(self.l2(x))
        x = F.relu(self.l3(x))
        return self.q_head(x)