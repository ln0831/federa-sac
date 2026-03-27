import torch
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.tensorboard import SummaryWriter
from torch.optim.lr_scheduler import CosineAnnealingLR
import numpy as np
import os
import time
import importlib
import argparse 
from networks import LocalActor 
from networks_baselines import CentralizedCritic 
from fmasac_utils import MultiAgentReplayBuffer, soft_update, hard_update

class Opts:
    def __init__(self):
        parser = argparse.ArgumentParser(description="MASAC Baseline Training (Full Metrics)")
        parser.add_argument('--case', type=str, default='33', choices=['33', '69', '141', 'ober'], help="Select case")
        parser.add_argument('--gpu', type=str, default='0')
        parser.add_argument('--epochs', type=int, default=None)
        
        args = parser.parse_args()
        self.case_name = args.case
        
        # 保持与 FMASAC 一致的配置
        if self.case_name == '33':
            self.num_agents = 2; self.env_module = 'env_33'
            default_ep = 400; self.batch_size = 256; self.hidden_dim = 256
            self.steps_per_epoch = 96
        elif self.case_name == '141':
            self.num_agents = 4; self.env_module = 'env_141'
            default_ep = 500; self.batch_size = 64; self.hidden_dim = 256
            self.steps_per_epoch = 96
        elif self.case_name == 'ober': # [修复] 单独处理 oberrhein 文件名
            self.num_agents = 4; self.env_module = 'env_oberrhein'
            default_ep = 800; self.batch_size = 128; self.hidden_dim = 512
            self.steps_per_epoch = 96
        else: # 69
            self.num_agents = 4; self.env_module = f'env_{self.case_name}'
            default_ep = 800; self.batch_size = 128; self.hidden_dim = 512
            self.steps_per_epoch = 96

        self.epochs = args.epochs if args.epochs is not None else default_ep
        self.lr = 3e-4
        self.gamma = 0.95
        self.tau = 0.005
        self.buffer_size = 100000 
        self.start_steps = 2000
        self.update_every = 50
        self.update_times = 50
        self.val_interval = 5 # 每5轮验证一次
        self.val_episodes = 5
        
        if torch.cuda.is_available():
            self.device = torch.device(f"cuda:{args.gpu}")
        else:
            self.device = torch.device("cpu")

# 验证函数
def validate(env, actors, opts, step, tb_logger):
    avg_ret = 0.0
    for _ in range(opts.val_episodes):
        obs_list = env.reset()
        ep_ret = 0
        
        for _ in range(opts.steps_per_epoch):
            actions = []
            with torch.no_grad():
                for i in range(opts.num_agents):
                    o = torch.FloatTensor(obs_list[i]).unsqueeze(0).to(opts.device)
                    # 验证时直接取均值，不采样
                    a, _ = actors[i].forward(o) 
                    actions.append(a.cpu().numpy()[0])
            
            next_obs, rewards, done, _ = env.step(actions)
            obs_list = next_obs
            ep_ret += sum(rewards)
            if done: break
        avg_ret += ep_ret
    avg_ret /= opts.val_episodes
    
    if tb_logger:
        tb_logger.add_scalar('validate/return', avg_ret, step)
    return avg_ret

def main():
    opts = Opts()
    try:
        dist_net_module = importlib.import_module(opts.env_module)
        DistNetEnv = dist_net_module.DistNetEnv
    except ImportError as e:
        print(f"Error: {e}"); return
    
    run_id = time.strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join('./logs', f"MASAC_{opts.case_name}_{run_id}")
    tb_logger = SummaryWriter(log_path)
    
    print(f"🚀 Start Training MASAC (Baseline): {opts.case_name}")
    
    env = DistNetEnv(num_agents=opts.num_agents)
    val_env = DistNetEnv(num_agents=opts.num_agents) 
    
    obs_dims = [space.shape[0] for space in env.observation_space]
    act_dims = [space.shape[0] for space in env.action_space]
    
    total_obs_dim = sum(obs_dims)
    total_act_dim = sum(act_dims)
    
    # 网络初始化
    actors = [LocalActor(o, a, hidden_dim=opts.hidden_dim).to(opts.device) for o, a in zip(obs_dims, act_dims)]
    critic = CentralizedCritic(total_obs_dim, total_act_dim, hidden_dim=opts.hidden_dim).to(opts.device)
    target_critic = CentralizedCritic(total_obs_dim, total_act_dim, hidden_dim=opts.hidden_dim).to(opts.device)
    hard_update(target_critic, critic)
    
    actor_optims = [optim.Adam(a.parameters(), lr=opts.lr) for a in actors]
    critic_optim = optim.Adam(critic.parameters(), lr=opts.lr)
    
    log_alphas = []
    alpha_optims = []
    target_entropy = -np.mean(act_dims) * 0.9
    for _ in range(opts.num_agents):
        la = torch.zeros(1, requires_grad=True, device=opts.device)
        with torch.no_grad(): la.fill_(np.log(0.2)) 
        log_alphas.append(la)
        alpha_optims.append(optim.Adam([la], lr=opts.lr))
    
    actor_schedulers = [CosineAnnealingLR(opt, T_max=opts.epochs, eta_min=opts.lr * 0.01) for opt in actor_optims]
    critic_scheduler = CosineAnnealingLR(critic_optim, T_max=opts.epochs, eta_min=opts.lr * 0.01)

    buffer = MultiAgentReplayBuffer(opts.buffer_size, opts.num_agents, obs_dims, act_dims)
    total_steps = 0
    
    for epoch in range(opts.epochs):
        obs_list = env.reset()
        ep_reward = 0
        loss_critic_sum = 0.0
        
        for t in range(opts.steps_per_epoch):
            actions = []
            if total_steps < opts.start_steps:
                for i in range(opts.num_agents):
                    actions.append(env.action_space[i].sample())
            else:
                with torch.no_grad():
                    for i in range(opts.num_agents):
                        o = torch.FloatTensor(obs_list[i]).unsqueeze(0).to(opts.device)
                        a, _ = actors[i].sample(o)
                        actions.append(a.cpu().numpy()[0])
            
            next_obs, rewards, done, _ = env.step(actions)
            buffer.add(obs_list, actions, rewards, next_obs, done)
            obs_list = next_obs
            ep_reward += sum(rewards)
            total_steps += 1
            
            if done: obs_list = env.reset()
            
            if total_steps > opts.start_steps and total_steps % opts.update_every == 0:
                for _ in range(opts.update_times):
                    b_obs, b_act, b_rew, b_next_obs, b_done = buffer.sample(opts.batch_size)
                    b_obs = [x.to(opts.device) for x in b_obs]
                    b_act = [x.to(opts.device) for x in b_act]
                    b_rew = b_rew.to(opts.device)
                    b_next_obs = [x.to(opts.device) for x in b_next_obs]
                    b_done = b_done.to(opts.device)
                    
                    global_obs = torch.cat(b_obs, dim=1)
                    global_act = torch.cat(b_act, dim=1)
                    global_next_obs = torch.cat(b_next_obs, dim=1)
                    
                    # 1. Update Critic
                    with torch.no_grad():
                        next_acts = []
                        next_log_probs = []
                        for i in range(opts.num_agents):
                            na, nlp = actors[i].sample(b_next_obs[i])
                            next_acts.append(na)
                            next_log_probs.append(nlp)
                        
                        global_next_act = torch.cat(next_acts, dim=1)
                        target_q = target_critic(global_next_obs, global_next_act)
                        
                        entropy_term = 0
                        for i in range(opts.num_agents):
                            alpha = log_alphas[i].exp()
                            entropy_term += alpha * next_log_probs[i]
                            
                        y = b_rew.sum(dim=1, keepdim=True) + opts.gamma * (1-b_done) * (target_q - entropy_term)
                    
                    current_q = critic(global_obs, global_act)
                    critic_loss = F.mse_loss(current_q, y)
                    loss_critic_sum += critic_loss.item()
                    
                    critic_optim.zero_grad()
                    critic_loss.backward()
                    critic_optim.step()
                    
                    # 2. Update Actors
                    for p in critic.parameters(): p.requires_grad = False
                    for i in range(opts.num_agents):
                        curr_a, curr_lp = actors[i].sample(b_obs[i])
                        full_act_list = [a.detach() for a in b_act]
                        full_act_list[i] = curr_a
                        global_act_input = torch.cat(full_act_list, dim=1)
                        
                        q_val = critic(global_obs, global_act_input)
                        alpha = log_alphas[i].exp().detach()
                        actor_loss = (alpha * curr_lp - q_val).mean()
                        
                        actor_optims[i].zero_grad()
                        actor_loss.backward()
                        actor_optims[i].step()
                        
                        # 3. Alpha
                        alpha_loss = -(log_alphas[i] * (curr_lp.detach() + target_entropy).mean())
                        alpha_optims[i].zero_grad()
                        alpha_loss.backward()
                        alpha_optims[i].step()
                        with torch.no_grad(): log_alphas[i].clamp_(min=-3.0)

                    for p in critic.parameters(): p.requires_grad = True
                    soft_update(target_critic, critic, opts.tau)

        for s in actor_schedulers: s.step()
        critic_scheduler.step()

        avg_loss = loss_critic_sum / (opts.steps_per_epoch * opts.update_times) if total_steps > opts.start_steps else 0
        
        tb_logger.add_scalar('train/epoch_reward', ep_reward, epoch)
        tb_logger.add_scalar('train/loss_critic', avg_loss, epoch)
        
        print(f"Epoch {epoch}: Reward {ep_reward:.2f} | Loss {avg_loss:.4f}")
        
        if epoch % opts.val_interval == 0:
            val_ret = validate(val_env, actors, opts, epoch, tb_logger)
            print(f"  --> Validation: {val_ret:.2f}")

if __name__ == "__main__":
    main()