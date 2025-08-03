# HollowKnight_RL_PPO

- 上版本问题：模型不能很好的学到图像信息，来区分状态。分辨率 128, 160 可能不够。模型学的更多是向量状态，但其实也没太多有效信息。
- 症状表现为：训练 step 少的情况，一方面由于策略学习不充分，model predict 的 deterministic=True 情况下，会重复输出同一个动作复读。

### 尝试解决方案
- 只用图像状态：[3, 224, 224]，预训练 Resnet18，按 ImageNet 归一化到 [-3, 3]
- 动作加入黑冲，下砸，去掉输出效率低的上劈
- 黑冲，下砸实现：用 sb3_contrib 的 MaskablePPO，实现 action_masks 方法。
- 奖励分数：玩家血量，boss血量，结束额外奖惩。
- 先学了 2w step，

<div style="text-align: center;">
  <img src="./images/reward.png" alt="reward" style="width: auto; height: auto;">
</div>

<div style="text-align: center;">
  <img src="./images/loss.png" alt="loss" style="width: auto; height: auto;">
</div>
