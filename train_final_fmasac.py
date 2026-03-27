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
from tqdm import tqdm

# ==========================================
# 1. 导入基础组件
# ==========================================
from networks import LocalActor, LocalCritic 
from fmasac_utils import MultiAgentReplayBuffer, soft_update, hard_update

# ==========================================
# 2. 导入 GNN 组件 (创新点 A: 拓扑感知)
# ==========================================
from networks_gnn import GraphMixer 
from gnn_utils import get_agent_adjacency

# ==========================================
# 3. 定义量化算子 (创新点 B: 通信高效 - 动态修复版)
# ==========================================
class QuantizeComm(torch.autograd.Function):
    """
    [核心修复] 动态自适应量化 + 随机舍入
    解决固定范围量化导致的梯度消失问题，防止模型崩溃。
    """
    @staticmethod
    def forward(ctx, input, bits=8):
        ctx.bits = bits
        
        # 1. 动态计算范围 (Dynamic Range)
        min_val = input.min()
        max_val = input.max()
        
        # 防止数值极其接近导致除以0
        if max_val - min_val < 1e-8:
            # 这种情况通常不需要量化，或者直接返回
            return input
            
        # 2. 计算量化步长
        levels = 2 ** bits - 1
        step = (max_val - min_val) / levels
        
        # 3. 归一化
        val_norm = (input - min_val) / step
        
        # 4. 前向传播：标准四舍五入
        val_int = torch.round(val_norm)
        
        # 5. 反量化 (模拟传输后的恢复值)
        val_q = val_int * step + min_val
        
        # 保存上下文用于反向传播
        ctx.save_for_backward(input)
        return val_q

    @staticmethod
    def backward(ctx, grad_output):
        # 反向传播：随机舍入 (Stochastic Rounding)
        # 保持梯度的统计期望值，防止微小梯度被截断为0
        
        bits = ctx.bits
        input, = ctx.saved_tensors
        
        # 1. 梯度的动态范围
        g_min = grad_output.min()
        g_max = grad_output.max()
        
        if g_max - g_min < 1e-9:
            return grad_output, None

        levels = 2 ** bits - 1
        step = (g_max - g_min) / levels
        
        # 2. 归一化
        g_norm = (grad_output - g_min) / step
        
        # 3. [关键] 随机舍入
        noise = torch.rand_like(g_norm)
        g_int = torch.floor(g_norm + noise)
        
        # 截断
        g_int = torch.clamp(g_int, 0, levels)
        
        # 4. 反量化
        grad_q = g_int * step + g_min
        
        return grad_q, None

def apply_quantization(tensor, bits):
    # 使用动态量化，无需手动指定 min/max
    return QuantizeComm.apply(tensor, bits)

# ==========================================
# 4. 定义安全计算工具 (创新点 C: 安全约束)
# ==========================================
def calc_voltage_violation(obs_list, v_min=0.90, v_max=1.10):
    total_linear_viol = 0.0
    total_squared_viol = 0.0
    for obs in obs_list:
        n = len(obs) // 3
        v_norm = obs[2*n:] 
        v_real = v_norm / 20.0 + 1.0
        lower = np.maximum(0, v_min - v_real)
        upper = np.maximum(0, v_real - v_max)
        total_linear_viol += np.sum(lower + upper)
        total_squared_viol += np.sum(lower**2 + upper**2)
    return total_linear_viol, total_squared_viol

# ==============================================================================
# 配置类
# ==============================================================================
class Opts:
    def __init__(self):
        parser = argparse.ArgumentParser(description="Final FMASAC: GNN + Safe + Quantized (Dynamic)")
        
        # 基础配置
        parser.add_argument('--case', type=str, default='33', choices=['33', '69', '141', 'ober'])
        parser.add_argument('--gpu', type=str, default='0')
        parser.add_argument('--epochs', type=int, default=None)
        parser.add_argument('--batch_size', type=int, default=None)
        parser.add_argument('--hidden_dim', type=int, default=None)
        
        # 创新点参数
        parser.add_argument('--bits', type=int, default=8, help="Quantization bits (e.g. 4, 8)")
        parser.add_argument('--lambda_lr', type=float, default=0.01, help="Safe RL dual learning rate")
        parser.add_argument('--init_lambda', type=float, default=10.0, help="Initial safety penalty")
        parser.add_argument('--target_cost', type=float, default=0.001, help="Safety constraint limit")
        
        # 训练参数
        parser.add_argument('--lr', type=float, default=3e-4)
        parser.add_argument('--auto_alpha', action='store_true', default=True)
        parser.add_argument('--init_alpha', type=float, default=0.2)
        parser.add_argument('--entropy_ratio', type=float, default=0.9)
        parser.add_argument('--grad_clip', type=float, default=1.0)
        parser.add_argument('--val_episodes', type=int, default=5)


        # [Topology partition & adjacency options]
        parser.add_argument('--no_contiguous_partition', action='store_true', default=False,
                    help="Disable topology-contiguous area partition (fallback to np.array_split).")
        parser.add_argument('--partition_seed', type=int, default=0, help="Seed for contiguous partition.")
        parser.add_argument('--adj_mode', type=str, default='inv_z', choices=['inv_z','count','binary'],
                    help="Inter-area adjacency weighting mode for GNN mixer.")

        args = parser.parse_args()
        self.case_name = args.case
        
        # 自动配置不同环境的参数
        if self.case_name == '33':
            self.num_agents = 2; self.env_module = 'env_33'
            default_ep = 400; default_bs = 256; default_hd = 256
            self.steps_per_epoch = 96
        elif self.case_name == '69':
            self.num_agents = 4; self.env_module = 'env_69'
            default_ep = 800; default_bs = 128; default_hd = 512
            self.steps_per_epoch = 96
        elif self.case_name == '141':
            self.num_agents = 4; self.env_module = 'env_141'
            default_ep = 500; default_bs = 64; default_hd = 256
            self.steps_per_epoch = 96
        elif self.case_name == 'ober':
            self.num_agents = 4; self.env_module = 'env_oberrhein'
            default_ep = 1000; default_bs = 256; default_hd = 512
            self.steps_per_epoch = 96

        self.epochs = args.epochs if args.epochs is not None else default_ep
        self.batch_size = args.batch_size if args.batch_size is not None else default_bs
        self.hidden_dim = args.hidden_dim if args.hidden_dim is not None else default_hd
        
        self.lr = args.lr
        self.bits = args.bits
        self.lambda_lr = args.lambda_lr
        self.init_lambda = args.init_lambda
        self.target_cost = args.target_cost
        
        self.auto_alpha = args.auto_alpha
        self.init_alpha = args.init_alpha
        self.entropy_ratio = args.entropy_ratio
        self.grad_clip = args.grad_clip
        self.val_episodes = args.val_episodes
        self.contiguous_partition = (not args.no_contiguous_partition)
        self.partition_seed = args.partition_seed
        self.adj_mode = args.adj_mode
        
        self.gamma = 0.95
        self.tau = 0.005
        self.buffer_size = 100000 
        self.start_steps = 2000 
        self.update_after = 2000 
        self.update_every = 50
        self.update_times = 50
        self.val_interval = 5
        
        self.log_dir = './logs'
        self.save_dir = './checkpoints'
        
        if torch.cuda.is_available():
            self.device = torch.device(f"cuda:{args.gpu}")
        else:
            self.device = torch.device("cpu")

# ==============================================================================
# 验证函数
# ==============================================================================
def validate(env, actors, opts, step, tb_logger):
    avg_ret = 0.0
    avg_viol = 0.0
    
    for _ in range(opts.val_episodes):
        obs_list = env.reset()
        ep_ret = 0
        ep_viol = 0
        
        for _ in range(opts.steps_per_epoch):
            actions = []
            with torch.no_grad():
                for i in range(opts.num_agents):
                    o = torch.FloatTensor(obs_list[i]).unsqueeze(0).to(opts.device)
                    a, _ = actors[i].forward(o)
                    actions.append(a.cpu().numpy()[0])
            
            next_obs, rewards, done, _ = env.step(actions)
            
            # 计算真实物理越限
            lin_v, _ = calc_voltage_violation(next_obs)
            ep_viol += lin_v
            
            obs_list = next_obs
            ep_ret += sum(rewards)
            if done: break
            
        avg_ret += ep_ret
        avg_viol += ep_viol
        
    avg_ret /= opts.val_episodes
    avg_viol /= opts.val_episodes
    
    if tb_logger:
        tb_logger.add_scalar('validate/return', avg_ret, step)
        tb_logger.add_scalar('validate/violation', avg_viol, step)
    return avg_ret

# ==============================================================================
# 主函数
# ==============================================================================
def main():
    opts = Opts()
    
    # 1. 加载环境
    try:
        dist_net_module = importlib.import_module(opts.env_module)
        DistNetEnv = dist_net_module.DistNetEnv
    except ImportError as e:
        print(f"Error loading {opts.env_module}: {e}")
        return

    # 日志名称体现所有创新点
    run_id = time.strftime("%Y%m%d-%H%M%S")
    log_name = f"Final-FMASAC_{opts.case_name}_GNN_Safe_Q{opts.bits}bit_{run_id}"
    log_path = os.path.join(opts.log_dir, log_name)
    tb_logger = SummaryWriter(log_path)
    
    print("=" * 60)
    print(f"🚀 Start Training FINAL FMASAC: {opts.case_name}")
    print(f"   [A] Architecture: GraphMixer (GAT-based Topology Aware)")
    print(f"   [B] Safety: Primal-Dual Lagrangian (Target Cost: {opts.target_cost})")
    print(f"   [C] Efficiency: {opts.bits}-bit Dynamic Quantization (Stochastic Rounding)")
    print("=" * 60)
    
    env = DistNetEnv(num_agents=opts.num_agents, contiguous_partition=opts.contiguous_partition, partition_seed=opts.partition_seed)
    val_env = DistNetEnv(num_agents=opts.num_agents, contiguous_partition=opts.contiguous_partition, partition_seed=opts.partition_seed)
    
    # 2. [GNN] 提取拓扑
    print("[GNN] Extracting Grid Topology...")
    adj_matrix = get_agent_adjacency(env.net, env.areas, device=opts.device)
    
    obs_dims = [space.shape[0] for space in env.observation_space]
    act_dims = [space.shape[0] for space in env.action_space]
    
    # 3. 初始化网络
    actors = [LocalActor(o, a, hidden_dim=opts.hidden_dim).to(opts.device) for o, a in zip(obs_dims, act_dims)]
    critics = [LocalCritic(o, a, hidden_dim=opts.hidden_dim).to(opts.device) for o, a in zip(obs_dims, act_dims)]
    target_critics = [LocalCritic(o, a, hidden_dim=opts.hidden_dim).to(opts.device) for o, a in zip(obs_dims, act_dims)]
    
    # [GNN] 使用 GraphMixer
    mixer_dim = 64 if opts.hidden_dim < 256 else 128
    mixer = GraphMixer(opts.num_agents, adj_matrix, hidden_dim=mixer_dim).to(opts.device)
    target_mixer = GraphMixer(opts.num_agents, adj_matrix, hidden_dim=mixer_dim).to(opts.device)
    
    # 4. [Safe] 拉格朗日乘子
    log_lambda = torch.zeros(1, requires_grad=True, device=opts.device)
    with torch.no_grad():
        log_lambda.fill_(np.log(opts.init_lambda))
    lambda_optim = optim.Adam([log_lambda], lr=opts.lambda_lr)
    
    # 5. 自动熵
    if opts.auto_alpha:
        target_entropy = -np.mean(act_dims) * opts.entropy_ratio
        log_alpha = torch.zeros(1, requires_grad=True, device=opts.device)
        with torch.no_grad():
            log_alpha.fill_(np.log(opts.init_alpha))
        alpha_optim = optim.Adam([log_alpha], lr=opts.lr)
    else:
        alpha_val = opts.init_alpha
    
    # 6. 优化器 & 调度器
    actor_optims = [optim.Adam(a.parameters(), lr=opts.lr) for a in actors]
    critic_optims = [optim.Adam(c.parameters(), lr=opts.lr) for c in critics]
    mixer_optim = optim.Adam(mixer.parameters(), lr=opts.lr)
    
    actor_schedulers = [CosineAnnealingLR(opt, T_max=opts.epochs, eta_min=opts.lr * 0.01) for opt in actor_optims]
    critic_schedulers = [CosineAnnealingLR(opt, T_max=opts.epochs, eta_min=opts.lr * 0.01) for opt in critic_optims]
    mixer_scheduler = CosineAnnealingLR(mixer_optim, T_max=opts.epochs, eta_min=opts.lr * 0.01)
    
    if opts.auto_alpha:
        alpha_scheduler = CosineAnnealingLR(alpha_optim, T_max=opts.epochs, eta_min=opts.lr * 0.01)
    
    hard_update(target_mixer, mixer)
    for tc, c in zip(target_critics, critics):
        hard_update(tc, c)
        
    buffer = MultiAgentReplayBuffer(opts.buffer_size, opts.num_agents, obs_dims, act_dims)
    best_ret = -float('inf')
    total_steps = 0
    
    # ==========================================================================
    # Training Loop
    # ==========================================================================
    for epoch in range(opts.epochs):
        obs_list = env.reset()
        epoch_loss_sum = 0.0
        epoch_viol_sum = 0.0
        epoch_critic_loss_sum = 0.0
        current_ep_reward = 0
        finished_ep_rewards = []
        update_counts = 0
        
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
            
            next_obs, _, done, info = env.step(actions)
            
            # --- [Safe] 动态计算 Reward ---
            p_loss = info['p_loss'] if 'p_loss' in info else 0.0
            linear_v, squared_v = calc_voltage_violation(next_obs)
            total_violation = linear_v + 5.0 * squared_v
            
            current_lambda = log_lambda.exp().item()
            
            # Reward = -Loss - Lambda * Violation
            safe_reward_val = - (p_loss * 10.0) - current_lambda * (200.0 * total_violation)
            rewards = [safe_reward_val * 0.01] * opts.num_agents 
            
            epoch_loss_sum += p_loss
            epoch_viol_sum += linear_v
            current_ep_reward += sum(rewards)
            
            buffer.add(obs_list, actions, rewards, next_obs, done)
            obs_list = next_obs
            total_steps += 1
            
            if done:
                obs_list = env.reset()
                finished_ep_rewards.append(current_ep_reward)
                current_ep_reward = 0
            
            if total_steps > opts.update_after and total_steps % opts.update_every == 0:
                for _ in range(opts.update_times):
                    update_counts += 1
                    b_obs, b_act, b_rew, b_next_obs, b_done = buffer.sample(opts.batch_size)
                    b_obs = [x.to(opts.device) for x in b_obs]
                    b_act = [x.to(opts.device) for x in b_act]
                    b_rew = b_rew.to(opts.device)
                    b_next_obs = [x.to(opts.device) for x in b_next_obs]
                    b_done = b_done.to(opts.device)
                    
                    if opts.auto_alpha:
                        alpha = log_alpha.exp()
                    else:
                        alpha = opts.init_alpha
                    
                    # === 1. Update Critic (带量化) ===
                    with torch.no_grad():
                        tc_list, te_list, next_lp_list = [], [], []
                        for i in range(opts.num_agents):
                            na, nlp = actors[i].sample(b_next_obs[i])
                            tc, te = target_critics[i](b_next_obs[i], na)
                            
                            # [Quantization] 模拟上传 Target Critic 值 (Dynamic)
                            tc = apply_quantization(tc, opts.bits)
                            te = apply_quantization(te, opts.bits)
                            
                            tc_list.append(tc); te_list.append(te); next_lp_list.append(nlp)
                        
                        # [GNN Mixer]
                        tf = target_mixer(torch.cat(tc_list, dim=1))
                        q_next = tf + sum(te_list) - alpha * sum(next_lp_list)
                        q_target = b_rew.sum(1, keepdim=True) + opts.gamma * (1-b_done) * q_next
                    
                    lc_list, le_list = [], []
                    for i in range(opts.num_agents):
                        c, e = critics[i](b_obs[i], b_act[i])
                        
                        # [Quantization] 模拟上传 Current Critic 值 (Dynamic)
                        c = apply_quantization(c, opts.bits)
                        e = apply_quantization(e, opts.bits)
                        
                        lc_list.append(c); le_list.append(e)
                    
                    # [GNN Mixer]
                    q_pred = mixer(torch.cat(lc_list, dim=1)) + sum(le_list)
                    loss_q = F.mse_loss(q_pred, q_target)
                    epoch_critic_loss_sum += loss_q.item()
                    
                    mixer_optim.zero_grad()
                    for opt in critic_optims: opt.zero_grad()
                    loss_q.backward() # [Stochastic Gradient Quantization happens here]
                    
                    if opts.grad_clip > 0:
                        torch.nn.utils.clip_grad_norm_(mixer.parameters(), opts.grad_clip)
                        for c in critics:
                            torch.nn.utils.clip_grad_norm_(c.parameters(), opts.grad_clip)
                            
                    mixer_optim.step()
                    for opt in critic_optims: opt.step()
                    
                    # === 2. Update Actor (带量化) ===
                    for i in range(opts.num_agents):
                        curr_a, curr_lp = actors[i].sample(b_obs[i])
                        c_new, e_new = critics[i](b_obs[i], curr_a)
                        
                        # [Quantization]
                        c_inputs = [c.detach() for c in lc_list]
                        c_inputs[i] = apply_quantization(c_new, opts.bits)
                        e_new_q = apply_quantization(e_new, opts.bits)
                        
                        # [GNN Mixer]
                        f_val = mixer(torch.cat(c_inputs, dim=1))
                        
                        loss_actor = - (f_val + e_new_q - alpha.detach() * curr_lp).mean()
                        
                        actor_optims[i].zero_grad()
                        loss_actor.backward()
                        if opts.grad_clip > 0:
                            torch.nn.utils.clip_grad_norm_(actors[i].parameters(), opts.grad_clip)
                        actor_optims[i].step()
                        
                    # === 3. Update Alpha ===
                    if opts.auto_alpha:
                        avg_log_prob = sum([lp.mean() for lp in next_lp_list]) / opts.num_agents
                        alpha_loss = -(log_alpha * (avg_log_prob.detach() + target_entropy)).mean()
                        alpha_optim.zero_grad()
                        alpha_loss.backward()
                        alpha_optim.step()
                        with torch.no_grad():
                            log_alpha.clamp_(min=-3.0)

                    # === 4. [Safe] Update Lambda ===
                    batch_viol_sum = 0
                    for obs_tensor in b_next_obs:
                        n = obs_tensor.shape[1] // 3
                        v_norm = obs_tensor[:, 2*n:]
                        v_real = v_norm / 20.0 + 1.0
                        viol = torch.relu(0.9 - v_real) + torch.relu(v_real - 1.1)
                        batch_viol_sum += viol.sum()
                    avg_batch_viol = batch_viol_sum / opts.batch_size
                    
                    # Dual Ascent
                    lambda_loss = - (log_lambda.exp() * (opts.target_cost - avg_batch_viol.detach())).mean()
                    lambda_optim.zero_grad()
                    lambda_loss.backward()
                    lambda_optim.step()
                    with torch.no_grad(): log_lambda.clamp_(max=5.0)

                    # Soft Update
                    for i in range(opts.num_agents):
                        soft_update(target_critics[i], critics[i], opts.tau)
                    soft_update(target_mixer, mixer, opts.tau)
        
        # Scheduler
        for s in actor_schedulers: s.step()
        for s in critic_schedulers: s.step()
        mixer_scheduler.step()
        if opts.auto_alpha: alpha_scheduler.step()

        # Logging
        avg_loss = epoch_loss_sum / opts.steps_per_epoch
        avg_viol_log = epoch_viol_sum / opts.steps_per_epoch
        avg_critic_loss = epoch_critic_loss_sum / update_counts if update_counts > 0 else 0.0
        
        if len(finished_ep_rewards) > 0:
            avg_ep_reward = np.mean(finished_ep_rewards)
        else:
            avg_ep_reward = current_ep_reward
            
        cur_lambda = log_lambda.exp().item()
        cur_alpha = log_alpha.exp().item() if opts.auto_alpha else opts.init_alpha

        tb_logger.add_scalar('train/loss_mw', avg_loss, epoch)
        tb_logger.add_scalar('train/epoch_reward', avg_ep_reward, epoch)
        tb_logger.add_scalar('train/lambda', cur_lambda, epoch)
        tb_logger.add_scalar('train/violation_sum', avg_viol_log, epoch)
        tb_logger.add_scalar('train/loss_critic', avg_critic_loss, epoch)
        tb_logger.add_scalar('train/alpha', cur_alpha, epoch)
            
        tb_logger.flush()
        
        status_msg = "WARMUP" if total_steps < opts.start_steps else "TRAIN"
        print(f"Epoch {epoch} [{status_msg}]: R {avg_ep_reward:.2f} | Loss {avg_loss:.4f} | Viol {avg_viol_log:.4f} | Lam {cur_lambda:.2f}")
        
        if epoch % opts.val_interval == 0:
            val_ret = validate(val_env, actors, opts, epoch, tb_logger)
            print(f"  --> Validation: {val_ret:.2f}")
            
            if val_ret > best_ret:
                best_ret = val_ret
                if not os.path.exists(opts.save_dir): os.makedirs(opts.save_dir)
                # 保存模型
                torch.save({'mixer': mixer.state_dict(), 'actors': [a.state_dict() for a in actors]}, 
                           os.path.join(opts.save_dir, f'best_model_final_{opts.case_name}.pth'))

if __name__ == "__main__":
    main()