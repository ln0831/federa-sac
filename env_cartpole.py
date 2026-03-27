import gymnasium as gym
import numpy as np
from gymnasium import spaces

class DistNetEnv(gym.Env):
    def __init__(self, num_agents=1, contiguous_partition=True, partition_seed=0):
        # CartPole 本质是单智能体，所以强制 num_agents = 1
        self.num_agents = 1
        
        # 加载标准 CartPole 环境
        self.gym_env = gym.make("CartPole-v1")
        
        # 1. 包装观测空间
        # FMASAC 期待一个列表 [agent1_obs, agent2_obs...]
        self.observation_space = [self.gym_env.observation_space]

        # 2. 包装动作空间
        # FMASAC 是连续控制 (输出 -1 到 1 的浮点数)
        # CartPole 原本是离散的 (0, 1)，这里声明为连续空间
        # 我们在 step 里把连续值映射回离散值
        self.action_space = [spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)]

    def reset(self):
        obs, _ = self.gym_env.reset()
        # [关键] 强制转换为 float32 并包裹在列表中
        return [obs.astype(np.float32)]

    def step(self, actions):
        # actions 是一个列表，包含所有智能体的动作
        # 取出第一个智能体的动作 (是一个数组, e.g. [0.53])
        act_val = actions[0][0]
        
        # [连续 -> 离散映射]
        # 算法输出 > 0 -> 动作 1 (右)
        # 算法输出 <= 0 -> 动作 0 (左)
        act_discrete = 1 if act_val > 0 else 0
        
        next_obs, reward, terminated, truncated, info = self.gym_env.step(act_discrete)
        
        done = terminated or truncated
        
        # [关键] 保持返回格式与电力系统环境完全一致：
        # ([obs], [reward], done, info)
        return [next_obs.astype(np.float32)], [float(reward)], done, info

    def close(self):
        self.gym_env.close()