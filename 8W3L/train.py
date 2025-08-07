import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

from env import HollowKnightEnv
from sb3_contrib import MaskablePPO

from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.vec_env import VecNormalize




class ResNetFeatureExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space, features_dim=512):
        super().__init__(observation_space, features_dim)
        # 加载预训练的ResNet18（可换为ResNet34/50等）
        resnet = resnet18(weights=ResNet18_Weights.DEFAULT)
        # 去掉最后的全连接层
        self.resnet = nn.Sequential(*list(resnet.children())[:-1])
        self._features_dim = resnet.fc.in_features

    def forward(self, observations):
        # 输入shape: (batch, C, H, W)

        x = self.resnet(observations)
        x = x.view(x.size(0), -1)
        return x
    

policy_kwargs = dict(
    features_extractor_class=ResNetFeatureExtractor,
    features_extractor_kwargs=dict(features_dim=512),
)


train_env = HollowKnightEnv()
train_env = DummyVecEnv([lambda: Monitor(train_env)])
train_env = VecNormalize(train_env, norm_obs=False, norm_reward=True)



model = MaskablePPO(
    policy="CnnPolicy",
    env=train_env,
    policy_kwargs=policy_kwargs,
    verbose=1,
    
    # 🔧 关键修复参数
    n_steps=256,           # 减少rollout长度，提高更新频率
    learning_rate=2e-4,    # 大幅降低学习率（从3e-4到1e-4）
    n_epochs=4,            # 减少每次rollout的训练轮数
    target_kl= 0.05, 
    
    tensorboard_log="./logs/"
)

model.learn(total_timesteps=8_0000)
model.save('./logs/hollow_knight_model_stable_1.zip')



from sb3_contrib.common.maskable.utils import get_action_masks
from sb3_contrib import MaskablePPO
from env import HollowKnightEnv
import time

env = HollowKnightEnv()

model = MaskablePPO.load('./logs/hollow_knight_model_stable_1.zip')

obs, info = env.reset()
n_steps = 2000
for _ in range(n_steps):

    action_masks = get_action_masks(env)
    # print(action_masks)
    action = model.predict(obs, action_masks=action_masks, deterministic=True)[0]
    obs, reward, done, truncated, info = env.step(action)
    if done:
        # break
        obs, info = env.reset()