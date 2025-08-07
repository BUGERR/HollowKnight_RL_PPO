import gymnasium
from gymnasium import spaces
import numpy as np

from utils import get_frame_rgb, HpXy_getter, restart, boss_hp_bar_exists
import time

from Actions import *
from Reward import player_hp_reward, boss_hp_reward, done_reward

import cv2


IMG_SIZE = 224
# NUM_FRAME = 4

NUM_MOVE = 4
NUM_ATTACK = 5  # 攻击动作数量

NUM_STATE = 4 # player_hp, boss_hp, 如果放技能加上 player_souls。加上黑冲状态？


PLAYER_MAX_HP = 9
BOSS_MAX_HP = 900
PLAYER_MAX_SOULS = 99

SKILL_SOULS_COST = 33

SHADOW_DASH_STATE = 1  # 黑冲状态
NORMAL_DASH_STATE = 0  # 普通状态

DASH_DIS = 5.6



class HollowKnightEnv(gymnasium.Env):
    def __init__(self):
        super().__init__()

        self.image_shape = (3, IMG_SIZE, IMG_SIZE)

        self.action_space = spaces.MultiDiscrete([NUM_MOVE, NUM_ATTACK])
        self.observation_space = spaces.Box(low=-3.0, high=3.0, shape=self.image_shape, dtype=np.float32)

        self.prev_state = None

        self.epoch = 0
        self.time_step = 0
        # self.act_time_gap = 0.3

        self.Actions = [
            Move_Left, Move_Right, 
            Turn_Left,Turn_Right,# move
            Attack_Down, Mid_Jump_Attack, # jump x
            Attack, 
            # Attack_Up,   # attack
            Dash, 
            # Skill, 
            Skill_Down, # skill
        ]

        self.MOVE = [ 
            "Move_Left", "Move_Right", 
            "Turn_Left","Turn_Right"
                    ]
        self.ATTACK = [
            "Attack_Down", "Mid_Jump_Attack",
            "Attack", 
            # "Attack_Up", 
            "Dash", 
            # "Skill", 
            "Skill_Down", 
            # "Skill_Up"
            ]
        
        self.prev_time = 0

        self.action_mask = None

        self.boss_hp_bar = False

        self.epoch_reward = 0

        # self.pre_img = None

        # 添加一个持久的 getter 实例
        self.hp_getter = None

    
    def _get_frame(self):
        frame = get_frame_rgb()[180:600, 100:1080, :]
        frame_resized = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
        frame_resized = np.transpose(frame_resized, (2, 0, 1))  # 转换为 (C, H, W) 格式
        frame_resized = frame_resized.astype(np.float32) / 255.0

        # IMAGENET 均值和方差
        mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1)
        std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1)
        frame_resized = (frame_resized - mean) / std

        return frame_resized
    

    def _get_state_vector(self):
        # 复用 getter 实例
        if self.hp_getter is None:
            self.hp_getter = HpXy_getter()
        
        getter = self.hp_getter
        
        player_hp = getter.get_player_hp()
        boss_hp = getter.get_boss_hp(player_hp, self.boss_hp_bar)
        player_souls = getter.get_player_souls()
        player_shadow_dash_state = getter.get_player_dash_state()
        player_x, player_y = getter.get_player_xy()
        boss_x, boss_y = getter.get_boss_xy()

        state = {
            "player_hp": player_hp,
            "boss_hp": boss_hp,
            "player_souls": player_souls,
            "player_shadow_dash_state": player_shadow_dash_state,
            "player_x": player_x,
            "boss_x": boss_x,
        }

        return state

    # def _state_to_observation(self, state):
    #     observation = np.array([
    #         state["player_hp"] / PLAYER_MAX_HP, 
    #         state["boss_hp"] / BOSS_MAX_HP, 
    #         state["player_souls"] / PLAYER_MAX_SOULS,
    #         state["player_shadow_dash_state"]
    #     ], dtype=np.float32)

    #     return observation
    

    # def _calculate_time(self):
    #     # 不能执行太快，如果小于执行间隔，等待
    #     # 判断逻辑
    #     t = self.act_time_gap - (time.time() - self.prev_time)
    #     if t > 0:
    #         time.sleep(t)
    #     self.prev_time = time.time()
    #     # self.time_step += 1


    def _wait_to_see(self, attack_index):
        # 等待攻击动作执行完毕
        if attack_index == self.ATTACK.index("Dash"):
            action_time = 0.285
        elif attack_index == self.ATTACK.index("Skill_Down"):
            action_time = 0.655
        elif attack_index == self.ATTACK.index("Mid_Jump_Attack"):
            action_time = 0.45
        else:
            action_time = 0.275
        
        wait_time = action_time - (time.time() - self.prev_time)

        # print((time.time() - self.prev_time))

        if wait_time > 0:
            time.sleep(wait_time)

        self.prev_time = time.time()

        

    def action_masks(self):
        attack_mask = np.ones(NUM_ATTACK, dtype=bool)

        raw_state = self.prev_state

        # 根据状态更新动作掩码
        if raw_state["player_shadow_dash_state"] == NORMAL_DASH_STATE:
            attack_mask[self.ATTACK.index("Dash")] = 0

        # 冲刺距离
        
        if raw_state["player_souls"] < SKILL_SOULS_COST:
            # attack_mask[self.ATTACK.index("Skill")] = 0
            # attack_mask[self.ATTACK.index("Skill_Up")] = 0
            attack_mask[self.ATTACK.index("Skill_Down")] = 0
        
        move_mask = np.ones(NUM_MOVE, dtype=bool)
        action_mask = np.concatenate([move_mask, attack_mask])

        return action_mask
    

    def reset(self, *, seed = None, options = None):
        super().reset(seed=seed, options=options)

        restart()

        self.epoch += 1
        print(f"[RESET] 第{self.epoch}轮战斗")

        self.prev_time = time.time()

        self.boss_hp_bar = False

        self.epoch_reward = 0


        raw_state = self._get_state_vector()
        self.prev_state = raw_state

        image_observation = self._get_frame()

        # self.pre_img = image_observation

        observation = image_observation

        return observation, {}
        
    def step(self, action):
        if self._get_state_vector()["player_x"] >= 60:
            done = False
            truncated = True
            return self._get_frame(), 0, done, truncated, {}

        move_index, attack_index = action
        
        self.boss_hp_bar = boss_hp_bar_exists()

        # start_time = time.time()

        # 执行移动
        self.Actions[move_index]()
        # 执行攻击
        self.Actions[attack_index + NUM_MOVE]()

        # mid_time = time.time()
        
        self._wait_to_see(attack_index)

        # end_time = time.time()

        # if end_time - mid_time == 0:
        #     print(self.ATTACK[attack_index])

        # print(f"all time: {end_time - start_time:.3f} s, action time: {mid_time - start_time:.3f} s, gap time: {end_time - mid_time:.3f} s")


        self.time_step += 1

        # print(f"timestep:{self.time_step}, action:{self.MOVE[move_index], self.ATTACK[attack_index]}", end = "")

        raw_state = self._get_state_vector()

        # 计算奖励
        reward, done = self._get_reward_done(raw_state, self.prev_state, action)

        self.epoch_reward += reward

        # print(f" reward:{reward:.3f}, boss_hp:{raw_state['boss_hp']}, done:{done}")
        if done:
            print(f"time_step:{self.time_step}, boss_hp:{raw_state['boss_hp']}, epoch_reward:{self.epoch_reward:.3f}")

     
        image_observation = self._get_frame()
        # vector_observation = self._state_to_observation(raw_state)

        self.prev_state = raw_state


        observation = image_observation

        # self.pre_img = image_observation
 
        return observation, reward, done, False, {}
    

    def _get_reward_done(self, state, prev_state, action):
        move_index, attack_index = action

        done = state["player_hp"] <= 0 or state["boss_hp"] <= 0

        reward = 0.0
        reward += player_hp_reward(player_hp=state["player_hp"], prev_player_hp=prev_state["player_hp"])
        reward += boss_hp_reward(boss_hp=state["boss_hp"], prev_boss_hp=prev_state["boss_hp"])


        if done:
            reward += done_reward(player_hp=state["player_hp"], boss_hp=state["boss_hp"])

        # reward -= 0.05  # 每一步都惩罚一点，鼓励尽快结束战斗

        return reward, done

    def close(self):
        # 添加 close 方法清理资源
        if self.hp_getter:
            self.hp_getter.close_pm_process()
            self.hp_getter = None
