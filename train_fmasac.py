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
import re
import pickle 
from tqdm import tqdm

from networks import LocalActor, LocalCritic, GlobalMixer
from fmasac_utils import MultiAgentReplayBuffer, soft_update, hard_update

class Opts:
    def __init__(self):
        parser = argparse.ArgumentParser(description="FMASAC Final: Fixed Graph Error & Optimized")
        
        # [环境选择]
        parser.add_argument('--case', type=str, default='33', 
                            choices=['33', '69', '141', 'ober', 'cartpole'],
                            help="Select grid case")
        parser.add_argument('--gpu', type=str, default='0', help="GPU ID")
        parser.add_argument('--log_dir', type=str, default='./logs', help='TensorBoard log root directory')
        parser.add_argument('--save_dir', type=str, default='./checkpoints', help='Checkpoint output directory')
        parser.add_argument('--exp_name', type=str, default='', help='Optional experiment name for log/checkpoint naming')
        
        # [训练超参]
        parser.add_argument('--epochs', type=int, default=None)
        parser.add_argument('--batch_size', type=int, default=None)
        parser.add_argument('--hidden_dim', type=int, default=None)
        
        # [学习率分离]
        parser.add_argument('--actor_lr', type=float, default=None)
        parser.add_argument('--critic_lr', type=float, default=None)
        
        # [高级特性开关]
        parser.add_argument('--auto_alpha', action='store_true', default=True, help="Enable Auto-Alpha")
        parser.add_argument('--init_alpha', type=float, default=0.2, help="Initial temperature")
        parser.add_argument('--entropy_ratio', type=float, default=0.9, help="Target entropy ratio") # 稍微调高一点
        parser.add_argument('--grad_clip', type=float, default=1.0, help="Gradient clipping norm")
        parser.add_argument('--val_episodes', type=int, default=5)

        # [Topology change / outage settings]
        parser.add_argument('--topology_mode', type=str, default='static', choices=['static','random_reset'],
                            help="Network topology mode. 'random_reset' applies random line outages on every reset.")
        parser.add_argument('--outage_k', type=int, default=None,
                            help="Number of line outages per episode when topology_mode=random_reset. If omitted, use paper-style defaults per case.")
        parser.add_argument('--outage_policy', type=str, default='local', choices=['global','local'],
                            help="Outage sampling policy for random_reset. 'local' samples faults within an r-hop neighborhood (paper-style).")
        parser.add_argument('--outage_radius', type=int, default=2,
                            help="Neighborhood radius (in hops) for outage_policy=local.")
        parser.add_argument('--avoid_slack_hops', type=int, default=1,
                            help="Avoid faulting lines within <= this hop distance from the slack bus.")
        parser.add_argument('--topology_seed', type=int, default=0,
                            help="Base seed for deterministic outage sampling (seed + episode_idx).")


        # [Disturbance scenarios (A/B/C): tidal / step / combined]
        parser.add_argument('--disturbance', type=str, default='none',
                            choices=['none','tidal','step','tidal_step'],
                            help="Disturbance mode: A=tidal, C=tidal_step. B is controlled by topology_mode/outages.")
        parser.add_argument('--reset_load_mode', type=str, default='keep', choices=['keep','base'],
                            help="Load reset mode: keep env.reset random jitter, or force base loads (deterministic).")
        # tidal params
        parser.add_argument('--tidal_period', type=int, default=96, help='Period (steps) for tidal profile.')
        parser.add_argument('--tidal_load_base', type=float, default=1.0, help='Baseline load scale for tidal.')
        parser.add_argument('--tidal_load_amp', type=float, default=0.2, help='Amplitude for tidal load scale.')
        parser.add_argument('--tidal_pv_base', type=float, default=1.0, help='Baseline PV availability scale for tidal.')
        parser.add_argument('--tidal_pv_amp', type=float, default=0.5, help='Amplitude for tidal PV availability scale.')
        parser.add_argument('--tidal_phase', type=float, default=0.0, help='Phase (radians) for tidal sinusoid.')
        # step params
        parser.add_argument('--step_t', type=int, default=24, help='Step time (step index) for step disturbance.')
        parser.add_argument('--step_factor', type=float, default=1.2, help='Multiplicative factor for step disturbance.')
        parser.add_argument('--step_target', type=str, default='random_agent',
                            choices=['all','random_agent','agent0','agent1','agent2','agent3'],
                            help='Where to apply the step disturbance (loads).')
        parser.add_argument('--dist_seed', type=int, default=0, help='Seed for selecting step target per episode (deterministic).')

        args = parser.parse_args()

        # Disturbance settings
        self.disturbance = str(args.disturbance).lower()
        self.reset_load_mode = str(args.reset_load_mode).lower()
        self.tidal_period = int(args.tidal_period)
        self.tidal_load_base = float(args.tidal_load_base)
        self.tidal_load_amp = float(args.tidal_load_amp)
        self.tidal_pv_base = float(args.tidal_pv_base)
        self.tidal_pv_amp = float(args.tidal_pv_amp)
        self.tidal_phase = float(args.tidal_phase)
        self.step_t = int(args.step_t)
        self.step_factor = float(args.step_factor)
        self.step_target = str(args.step_target)
        self.dist_seed = int(args.dist_seed)
        self.case_name = args.case
        self.auto_alpha = args.auto_alpha
        self.init_alpha = args.init_alpha
        self.entropy_ratio = args.entropy_ratio
        self.grad_clip = args.grad_clip
        self.topology_mode = args.topology_mode
        self.outage_policy = str(args.outage_policy).lower()
        self.outage_radius = int(args.outage_radius)
        self.avoid_slack_hops = int(args.avoid_slack_hops)
        self.topology_seed = int(args.topology_seed)
        
        # --- 自动配置默认参数 (Auto-Config) ---
        base_alr = 3e-4
        base_clr = 3e-4
        
        if self.case_name == 'cartpole':
            self.num_agents = 1; self.env_module = 'env_cartpole'
            default_ep = 200; default_bs = 128; default_hd = 128
            default_alr = 3e-4; default_clr = 3e-4
            self.steps_per_epoch = 200
            self.gamma = 0.99
            
        elif self.case_name == '33':
            self.num_agents = 2; self.env_module = 'env_33'
            default_ep = 400
            default_bs = 256  # [关键修改] 增大 Batch Size 减少震荡
            default_hd = 256
            default_alr = 3e-4 # [关键修改] 降低 LR 防止发散
            default_clr = 3e-4
            self.steps_per_epoch = 96
            self.gamma = 0.95

        elif self.case_name == '69':
            self.num_agents = 4; self.env_module = 'env_69'
            default_ep = 800; default_bs = 128; default_hd = 512
            default_alr = base_alr; default_clr = base_clr
            self.steps_per_epoch = 96
            self.gamma = 0.9

        elif self.case_name == '141':
            self.num_agents = 4; self.env_module = 'env_141'
            default_ep = 500; default_bs = 64; default_hd = 256
            default_alr = base_alr; default_clr = base_clr
            self.steps_per_epoch = 96
            self.gamma = 0.9

        elif self.case_name == 'ober':
            self.num_agents = 4; self.env_module = 'env_oberrhein'
            default_ep = 1000; default_bs = 256; default_hd = 512
            default_alr = base_alr; default_clr = base_clr
            self.steps_per_epoch = 96
            self.gamma = 0.9

        # Outage default settings (only used when topology_mode=random_reset)
        default_outage_k = 0
        if str(self.topology_mode).lower() == 'random_reset':
            if self.case_name in {'33','69'}:
                default_outage_k = 3
            elif self.case_name in {'141','ober'}:
                default_outage_k = 4
        self.outage_k = int(args.outage_k) if args.outage_k is not None else int(default_outage_k)

        # 应用参数
        self.epochs = args.epochs if args.epochs is not None else default_ep
        self.batch_size = args.batch_size if args.batch_size is not None else default_bs
        self.hidden_dim = args.hidden_dim if args.hidden_dim is not None else default_hd
        self.actor_lr = args.actor_lr if args.actor_lr is not None else default_alr
        self.critic_lr = args.critic_lr if args.critic_lr is not None else default_clr
        self.val_episodes = args.val_episodes
        
        self.tau = 0.005
        
        # Buffer 和 热身配置
        self.buffer_size = 100000 
        self.start_steps = 2000 # [关键修改] 减少热身步数，尽快开始学习
        self.update_after = 2000 
        
        self.update_every = 50
        self.update_times = 50
        self.log_dir = str(args.log_dir)
        self.save_dir = str(args.save_dir)
        self.exp_name = str(args.exp_name).strip()
        self.exp_tag = re.sub(r"[^A-Za-z0-9._-]+", "_", self.exp_name).strip("._-") if self.exp_name else ''
        self.val_interval = 5 # 减少验证频率，加快训练
        
        if torch.cuda.is_available():
            self.device = torch.device(f"cuda:{args.gpu}")
        else:
            self.device = torch.device("cpu")

def validate(env, actors, opts, step, tb_logger):
    avg_ret = 0.0
    for _ in range(opts.val_episodes):
        obs_list = env.reset()
        
        # [修改] 移除归一化处理，直接使用 obs
        
        ep_ret = 0
        limit = 500 if opts.case_name == 'cartpole' else opts.steps_per_epoch
        
        for _ in range(limit):
            actions = []
            with torch.no_grad():
                for i in range(opts.num_agents):
                    o = torch.FloatTensor(obs_list[i]).unsqueeze(0).to(opts.device)
                    mean, _ = actors[i].forward(o)
                    a = torch.tanh(mean)  # deterministic action in [-1, 1]
                    actions.append(a.cpu().numpy()[0])
            
            next_obs, rewards, done, _ = env.step(actions)
            
            # [修改] 移除归一化处理
            
            obs_list = next_obs
            ep_ret += sum(rewards)
            if done: break
        avg_ret += ep_ret
    avg_ret /= opts.val_episodes
    
    if tb_logger:
        tb_logger.add_scalar('validate/return', avg_ret, step)
        tb_logger.flush()
    return avg_ret

def main():
    opts = Opts()
    
    try:
        dist_net_module = importlib.import_module(opts.env_module)
        DistNetEnv = dist_net_module.DistNetEnv
    except ImportError as e:
        print(f"Error loading {opts.env_module}: {e}")
        return

    run_id = time.strftime("%Y%m%d-%H%M%S")
    if opts.exp_tag:
        log_name = f"FMASAC_{opts.exp_tag}_{run_id}"
    else:
        log_name = f"FMASAC_{opts.case_name}_NoNorm_FixAlpha_{run_id}"
    log_path = os.path.join(opts.log_dir, log_name)
    tb_logger = SummaryWriter(log_path)
    
    print("=" * 60)
    print(f"🚀 Start Training: {opts.case_name} (Fixed Version)")
    print(f"   Buffer: {opts.buffer_size} | Warmup Steps: {opts.start_steps}")
    print(f"   Adv Settings: EntRatio={opts.entropy_ratio}, Clip={opts.grad_clip}, Normalization=OFF")
    print(f"   LR: Actor={opts.actor_lr}, Critic={opts.critic_lr}")
    print("=" * 60)
    
    if opts.case_name == 'cartpole':
        env = DistNetEnv(num_agents=opts.num_agents)
        val_env = DistNetEnv(num_agents=opts.num_agents)
    else:
        env = DistNetEnv(
            num_agents=opts.num_agents,
            topology_mode=opts.topology_mode,
            outage_k=opts.outage_k,
            topology_seed=opts.topology_seed,
            outage_policy=opts.outage_policy,
            outage_radius=opts.outage_radius,
            avoid_slack_hops=opts.avoid_slack_hops,
        )
        val_env = DistNetEnv(
            num_agents=opts.num_agents,
            topology_mode=opts.topology_mode,
            outage_k=opts.outage_k,
            topology_seed=opts.topology_seed,
            outage_policy=opts.outage_policy,
            outage_radius=opts.outage_radius,
            avoid_slack_hops=opts.avoid_slack_hops,
        )
    

    # --- Disturbance wrapper (A/B/C scenarios) ---
    if getattr(opts, 'disturbance', 'none') != 'none':
        from scenario_env import DisturbanceConfig, ScenarioWrapper
        cfg = DisturbanceConfig(
            mode=opts.disturbance,
            tidal_period=getattr(opts, 'tidal_period', 96),
            tidal_load_base=getattr(opts, 'tidal_load_base', 1.0),
            tidal_load_amp=getattr(opts, 'tidal_load_amp', 0.2),
            tidal_pv_base=getattr(opts, 'tidal_pv_base', 1.0),
            tidal_pv_amp=getattr(opts, 'tidal_pv_amp', 0.5),
            tidal_phase=getattr(opts, 'tidal_phase', 0.0),
            step_t=getattr(opts, 'step_t', 24),
            step_factor=getattr(opts, 'step_factor', 1.2),
            step_target=getattr(opts, 'step_target', 'random_agent'),
            dist_seed=getattr(opts, 'dist_seed', 0),
            reset_load_mode=getattr(opts, 'reset_load_mode', 'keep'),
            recompute_on_reset=True,
        )
        env = ScenarioWrapper(env, cfg)
        val_env = ScenarioWrapper(val_env, cfg)

    obs_dims = [space.shape[0] for space in env.observation_space]
    act_dims = [space.shape[0] for space in env.action_space]
    
    # [修改] 彻底移除 RunningMeanStd
    
    actors = [LocalActor(o, a, hidden_dim=opts.hidden_dim).to(opts.device) for o, a in zip(obs_dims, act_dims)]
    critics = [LocalCritic(o, a, hidden_dim=opts.hidden_dim).to(opts.device) for o, a in zip(obs_dims, act_dims)]
    target_critics = [LocalCritic(o, a, hidden_dim=opts.hidden_dim).to(opts.device) for o, a in zip(obs_dims, act_dims)]
    
    mixer_dim = 64 if opts.hidden_dim < 256 else 128
    mixer = GlobalMixer(opts.num_agents, hidden_dim=mixer_dim).to(opts.device)
    target_mixer = GlobalMixer(opts.num_agents, hidden_dim=mixer_dim).to(opts.device)
    
    if opts.auto_alpha:
        target_entropy = -np.mean(act_dims) * opts.entropy_ratio
        log_alpha = torch.zeros(1, requires_grad=True, device=opts.device)
        with torch.no_grad():
            log_alpha.fill_(np.log(opts.init_alpha))
        alpha_optim = optim.Adam([log_alpha], lr=opts.actor_lr)
        print(f"   [System] Auto-Alpha Enabled. Target Entropy: {target_entropy:.4f}")
    else:
        alpha_val = opts.init_alpha
    
    actor_optims = [optim.Adam(a.parameters(), lr=opts.actor_lr) for a in actors]
    critic_optims = [optim.Adam(c.parameters(), lr=opts.critic_lr) for c in critics]
    mixer_optim = optim.Adam(mixer.parameters(), lr=opts.critic_lr)
    
    actor_schedulers = [CosineAnnealingLR(opt, T_max=opts.epochs, eta_min=opts.actor_lr * 0.01) for opt in actor_optims]
    critic_schedulers = [CosineAnnealingLR(opt, T_max=opts.epochs, eta_min=opts.critic_lr * 0.01) for opt in critic_optims]
    mixer_scheduler = CosineAnnealingLR(mixer_optim, T_max=opts.epochs, eta_min=opts.critic_lr * 0.01)
    if opts.auto_alpha:
        alpha_scheduler = CosineAnnealingLR(alpha_optim, T_max=opts.epochs, eta_min=opts.actor_lr * 0.01)
    
    hard_update(target_mixer, mixer)
    for tc, c in zip(target_critics, critics):
        hard_update(tc, c)
        
    buffer = MultiAgentReplayBuffer(opts.buffer_size, opts.num_agents, obs_dims, act_dims)
    best_ret = -float('inf')
    total_steps = 0
    
    for epoch in range(opts.epochs):
        obs_list = env.reset()
        
        # [修改] 移除归一化更新和应用
        
        epoch_ret = 0
        epoch_loss_sum = 0.0
        current_ep_reward = 0
        finished_ep_rewards = []
        
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
            
            next_obs, rewards, done, info = env.step(actions)
            
            # [修改] 移除归一化应用
            
            # [可选] 对 Reward 进行缩放 (tanh) 可以保留，也可以去掉，取决于 Env 里的缩放
            # 如果 Env 里已经是 -1 ~ 0 了，这里可以不用 tanh
            scaled_rewards = rewards 
            
            current_ep_reward += sum(rewards)
            if "p_loss" in info: epoch_loss_sum += info["p_loss"]
            
            buffer.add(obs_list, actions, scaled_rewards, next_obs, done)
            
            obs_list = next_obs
            total_steps += 1
            
            if done:
                obs_list = env.reset()
                # [修改] 移除归一化
                
                finished_ep_rewards.append(current_ep_reward)
                current_ep_reward = 0
            
            # [更新网络]
            if total_steps > opts.update_after and total_steps % opts.update_every == 0:
                for _ in range(opts.update_times):
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
                    
                    # --- Critic ---
                    with torch.no_grad():
                        tc_list, te_list, next_lp_list = [], [], []
                        for i in range(opts.num_agents):
                            na, nlp = actors[i].sample(b_next_obs[i])
                            tc, te = target_critics[i](b_next_obs[i], na)
                            tc_list.append(tc); te_list.append(te); next_lp_list.append(nlp)
                        
                        tf = target_mixer(torch.cat(tc_list, dim=1))
                        q_next = tf + sum(te_list) - alpha * sum(next_lp_list)
                        q_target = b_rew.sum(1, keepdim=True) + opts.gamma * (1-b_done) * q_next
                    
                    lc_list, le_list = [], []
                    for i in range(opts.num_agents):
                        c, e = critics[i](b_obs[i], b_act[i])
                        lc_list.append(c); le_list.append(e)
                    
                    q_pred = mixer(torch.cat(lc_list, dim=1)) + sum(le_list)
                    loss_q = F.mse_loss(q_pred, q_target)
                    
                    mixer_optim.zero_grad()
                    for opt in critic_optims: opt.zero_grad()
                    loss_q.backward()
                    
                    if opts.grad_clip > 0:
                        torch.nn.utils.clip_grad_norm_(mixer.parameters(), opts.grad_clip)
                        for c in critics:
                            torch.nn.utils.clip_grad_norm_(c.parameters(), opts.grad_clip)
                            
                    mixer_optim.step()
                    for opt in critic_optims: opt.step()
                    
                    # --- Actor ---
                    current_log_prob_sum = 0
                    for i in range(opts.num_agents):
                        curr_a, curr_lp = actors[i].sample(b_obs[i])
                        current_log_prob_sum += curr_lp.mean()
                        
                        c_new, e_new = critics[i](b_obs[i], curr_a)
                        c_inputs = [c.detach() for c in lc_list]
                        c_inputs[i] = c_new
                        f_val = mixer(torch.cat(c_inputs, dim=1))
                        
                        # [关键修复] alpha.detach()
                        loss_actor = - (f_val + e_new - alpha.detach() * curr_lp).mean()
                        
                        actor_optims[i].zero_grad()
                        loss_actor.backward()
                        if opts.grad_clip > 0:
                            torch.nn.utils.clip_grad_norm_(actors[i].parameters(), opts.grad_clip)
                        actor_optims[i].step()
                        
                    # --- Alpha ---
                    if opts.auto_alpha:
                        avg_log_prob = current_log_prob_sum / opts.num_agents
                        alpha_loss = -(log_alpha * (avg_log_prob.detach() + target_entropy)).mean()
                        alpha_optim.zero_grad()
                        alpha_loss.backward()
                        alpha_optim.step()
                        
                        # [关键修复] 限制 Alpha 不小于 0.05
                        with torch.no_grad():
                            log_alpha.clamp_(min=-3.0)

                    # Soft Update
                    for i in range(opts.num_agents):
                        soft_update(target_critics[i], critics[i], opts.tau)
                    soft_update(target_mixer, mixer, opts.tau)
        
        # Scheduler
        for sched in actor_schedulers: sched.step()
        for sched in critic_schedulers: sched.step()
        mixer_scheduler.step()
        if opts.auto_alpha: alpha_scheduler.step()
        
        # Logging
        avg_loss_mw = epoch_loss_sum / opts.steps_per_epoch
        if len(finished_ep_rewards) > 0:
            avg_ep_reward = np.mean(finished_ep_rewards)
        else:
            avg_ep_reward = current_ep_reward
            
        # [修复 Alpha 显示报错] 无论是否更新，都从 log_alpha 读取
        if opts.auto_alpha:
            current_alpha_val = log_alpha.exp().item()
        else:
            current_alpha_val = opts.init_alpha

        tb_logger.add_scalar('train/loss_mw', avg_loss_mw, epoch)
        tb_logger.add_scalar('train/epoch_reward', avg_ep_reward, epoch)
        tb_logger.add_scalar('train/actor_lr', mixer_scheduler.get_last_lr()[0], epoch)
        tb_logger.add_scalar('train/alpha', current_alpha_val, epoch)
            
        tb_logger.flush()
        
        status_msg = "WARMUP" if total_steps < opts.start_steps else "TRAIN"
        print(
            f"Epoch {epoch} [{status_msg}]: RewardSum {avg_ep_reward:.2f} | Reward/Step {avg_ep_reward/opts.steps_per_epoch:.2f}, "
            f"Loss {avg_loss_mw:.4f} MW, Alpha {current_alpha_val:.3f}"
        )
        
        if epoch % opts.val_interval == 0:
            val_ret = validate(val_env, actors, opts, epoch, tb_logger)
            print(
                f"  --> Validation: Sum {val_ret:.2f} | PerStep {val_ret/opts.steps_per_epoch:.2f} (Best: {best_ret:.2f})"
            )
            
            if val_ret > best_ret:
                best_ret = val_ret
                if not os.path.exists(opts.save_dir): os.makedirs(opts.save_dir)
                
                save_dict = {
                    'mixer': mixer.state_dict(),
                    'actors': [a.state_dict() for a in actors],
                }
                legacy_path = os.path.join(opts.save_dir, f'best_model_{opts.case_name}.pth')
                if opts.exp_tag:
                    exp_path = os.path.join(opts.save_dir, f'best_{opts.exp_tag}.pth')
                    torch.save(save_dict, exp_path)
                    if exp_path != legacy_path:
                        torch.save(save_dict, legacy_path)
                else:
                    torch.save(save_dict, legacy_path)

if __name__ == "__main__":
    main()