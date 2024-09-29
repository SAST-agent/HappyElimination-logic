import random
from collections import deque

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from core.GymEnvironment import EliminationEnv

device = "cuda" if torch.cuda.is_available() else "cpu"

# DQN 模型
class DQN(nn.Module):

    def __init__(self, output_dim):
        super(DQN, self).__init__()
        self.ct1 = nn.ConvTranspose2d(1, 64, 3)
        self.ct2 = nn.Conv2d(64, 64, 3)
        self.fc1 = nn.Linear(25600, 2048)
        self.fc2 = nn.Linear(2048, 2048)
        self.fc3 = nn.Linear(2048, output_dim)

    def forward(self, x):
        B, W, H = x.shape
        x = self.ct1(x.view(B, 1, W, H))
        # print("first", x.shape)
        x = torch.tanh(x)
        x = self.ct2(x)
        # print("second", x.shape)
        x = torch.flatten(x, start_dim=1)
        # print("third", x.shape)
        x = torch.tanh(self.fc1(x))
        x = torch.tanh(self.fc2(x))
        x = self.fc3(x)
        return x

class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        state, action, reward, next_state, done = zip(
            *random.sample(self.buffer, batch_size))
        return np.stack(state), action, reward, np.stack(next_state), done

    def size(self):
        return len(self.buffer)


def epsilon_greedy_action(q_values, epsilon):
    if random.random() < epsilon:
        operation_num = random.randint(0, q_values.size(-1) - 1)
    else:
        operation_num = q_values.argmax().item()

    d = operation_num % 20
    c = int(((operation_num - d) / 20) % 20)
    b = int(((operation_num - c * 20 - d) / 400) % 20)
    a = int(((operation_num - d - c * 20 - b * 400) / 8000) % 20)

    return [a, b, c, d]


def train_dqn(
    env,
    num_episodes=1000,
    batch_size=16,
    gamma=0.99,
    lr=1e-3,
    epsilon_start=1.0,
    epsilon_end=0.2,
    epsilon_decay=10000,
):
    # 获取状态和动作空间维度
    state_dim = (
        env.observation_space.shape[0] * env.observation_space.shape[1]
    )  # 状态为20x20的张量
    action_dim = env.action_space.n  # 动作是可能的交换操作数量

    # 初始化Q网络和目标Q网络
    q_net = DQN(action_dim).to(device)
    target_q_net = DQN(action_dim).to(device)
    target_q_net.load_state_dict(q_net.state_dict())

    optimizer = optim.Adam(q_net.parameters(), lr=lr)
    replay_buffer = ReplayBuffer(capacity=10000)

    epsilon = epsilon_start
    epsilon_decay_rate = (epsilon_start - epsilon_end) / epsilon_decay

    for episode in range(num_episodes):
        state, _ = env.reset()
        episode_reward = 0
        done = False

        while not done:
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
            q_values = q_net(state_tensor)

            action = epsilon_greedy_action(q_values, epsilon)

            next_state, reward, done = env.step(action)

            # 存储经验到回放缓冲区
            replay_buffer.push(
                state,
                action[0] * 8000 + action[1] * 400 + action[2] * 20 + action[3],
                reward,
                next_state,
                done,
            )

            state = next_state
            episode_reward += reward

            # 经验回放训练
            if replay_buffer.size() >= batch_size:
                batch_state, batch_action, batch_reward, batch_next_state, batch_done = replay_buffer.sample(
                    batch_size)

                batch_state_tensor = torch.FloatTensor(batch_state).to(device)
                batch_action_tensor = torch.LongTensor(batch_action).to(device)
                batch_reward_tensor = torch.FloatTensor(
                    batch_reward).to(device)
                batch_next_state_tensor = torch.FloatTensor(
                    batch_next_state).to(device)
                batch_done_tensor = torch.FloatTensor(batch_done).to(device)

                # print("state", batch_state_tensor.shape)

                q_values = q_net(batch_state_tensor)
                next_q_values = target_q_net(batch_next_state_tensor)

                # 计算Q目标值
                target_q_values = batch_reward_tensor + gamma * \
                    (1 - batch_done_tensor) * next_q_values.max(1)[0]

                # 获取选择的动作的Q值
                q_value = q_values.gather(
                    1, batch_action_tensor.unsqueeze(1)).squeeze(1)

                # 计算损失
                loss = nn.functional.mse_loss(
                    q_value, target_q_values.detach())

                # 反向传播和优化
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            # 更新epsilon
            epsilon = max(epsilon_end, epsilon - epsilon_decay_rate)

        # 更新目标网络参数
        if episode % 10 == 0:
            target_q_net.load_state_dict(q_net.state_dict())

        if episode % 50 == 0:
            torch.save(target_q_net.state_dict(), "model.pt")

        print(
            f"Episode {episode}, Total Reward: {episode_reward}, Epsilon: {epsilon}, loss: {loss.item()}"
        )

    return q_net


# 初始化环境
env = EliminationEnv()  # 使用你的消消乐环境

# 训练模型
trained_q_net = train_dqn(env, num_episodes=100000)
