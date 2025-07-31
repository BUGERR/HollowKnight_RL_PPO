import gymnasium
from gymnasium import spaces
import numpy as np

from utils import get_frame_rgb, HpXy_getter, restart, boss_hp_bar_exists
import time

from Actions import *
from Reward import player_hp_reward, boss_hp_reward, done_reward

import cv2


IMG_SIZE = 128
NUM_FRAME = 4

NUM_MOVE = 4
NUM_ATTACK = 5  # 攻击动作数量

NUM_STATE = 4 # player_hp, boss_hp, 如果放技能加上 player_souls。加上黑冲状态？


PLAYER_MAX_HP = 9
BOSS_MAX_HP = 900
PLAYER_MAX_SOULS = 99

SKILL_SOULS_COST = 33

SHADOW_DASH_STATE = 1  # 黑冲状态
NORMAL_DASH_STATE = 0  # 普通状态




class HollowKnightEnv(gymnasium.Env):
    def __init__(self):
        super().__init__()

        self.image_shape = (IMG_SIZE, IMG_SIZE, 3, NUM_FRAME)

        self.action_space = spaces.MultiDiscrete([NUM_MOVE, NUM_ATTACK])
        self.observation_space = spaces.Dict({
            "image": spaces.Box(low=0, high=255, shape=(IMG_SIZE, IMG_SIZE, 3 * NUM_FRAME), dtype=np.uint8), 
            "vector": spaces.Box(low=0.0, high=1.0, shape=(NUM_STATE,), dtype=np.float32),
        })
        self.frame_stack = np.zeros(self.image_shape, dtype=np.uint8)

        self.prev_state = None

        self.epoch = 0
        self.time_step = 0
        self.act_time_gap = 0.08

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

    
    def _get_frame(self):
        frame = get_frame_rgb()
        frame_resized = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
        return frame_resized.astype(np.uint8)

    # ------ 帧栈更新 ------
    def _update_stack(self, new_frame):
        # self.frame_stack = new_frame.copy()  # 重置为新帧

        self.frame_stack = np.roll(self.frame_stack, -1, axis=3)  # 滚动更新
        self.frame_stack[:, :, :, -1] = new_frame
        return self.frame_stack.copy()
    

    def _get_state_vector(self):
        getter = HpXy_getter()
        
        player_hp = getter.get_player_hp()
        boss_hp = getter.get_boss_hp(player_hp, self.boss_hp_bar)
        player_souls = getter.get_player_souls()
        player_shadow_dash_state = getter.get_player_dash_state()

        state = {
            "player_hp": player_hp,
            "boss_hp": boss_hp,
            "player_souls": player_souls,
            "player_shadow_dash_state": player_shadow_dash_state,
        }

        return state

    def _state_to_observation(self, state):
        observation = np.array([
            state["player_hp"] / PLAYER_MAX_HP, 
            state["boss_hp"] / BOSS_MAX_HP, 
            state["player_souls"] / PLAYER_MAX_SOULS,
            state["player_shadow_dash_state"]
        ], dtype=np.float32)

        return observation
    

    def _calculate_time(self):
        t = self.act_time_gap - (time.time() - self.prev_time)
        if t > 0:
            time.sleep(t)
        self.prev_time = time.time()
        # self.time_step += 1


    def _get_action_mask(self, raw_state):
        action_mask = np.ones(NUM_ATTACK, dtype=bool)

        # 根据状态更新动作掩码
        if raw_state["player_shadow_dash_state"] == NORMAL_DASH_STATE:
            action_mask[self.ATTACK.index("Dash")] = 0
        
        if raw_state["player_souls"] < SKILL_SOULS_COST:
            # action_mask[self.ATTACK.index("Skill")] = 0
            # action_mask[self.ATTACK.index("Skill_Up")] = 0
            action_mask[self.ATTACK.index("Skill_Down")] = 0

        return action_mask

    def reset(self, *, seed = None, options = None):
        super().reset(seed=seed, options=options)

        restart()

        self.epoch += 1
        print(f"[RESET] 第{self.epoch}轮战斗")

        self.prev_time = time.time()

        self.boss_hp_bar = False

        self.frame_stack.fill(0)
        frame = self._get_frame()
        for _ in range(NUM_FRAME):
            self._update_stack(frame)

        raw_state = self._get_state_vector()
        self.prev_state = raw_state

        image_observation = self.frame_stack.copy().reshape(IMG_SIZE, IMG_SIZE, 3 * NUM_FRAME)
        vector_observation = self._state_to_observation(raw_state)

        self.action_mask = self._get_action_mask(raw_state)

        observation = {
            "image": image_observation,
            "vector": vector_observation,
        }

        return observation, {}
        
    def step(self, action):
        move_index, attack_index = action

        attack_mask = self.action_mask

        if attack_mask[attack_index] == 0:
            self.time_step += 1
            raw_state = self._get_state_vector()
            new_frame = self._get_frame()
            image_observation = self._update_stack(new_frame).reshape(IMG_SIZE, IMG_SIZE, 3 * NUM_FRAME)
            vector_observation = self._state_to_observation(raw_state)
            observation = {
                "image": image_observation,
                "vector": vector_observation,
            }
            return observation, -1.0, False, False, {}
        
        self.boss_hp_bar = boss_hp_bar_exists()

        self._calculate_time()

        # 执行移动
        self.Actions[move_index]()

        self._calculate_time()

        # 执行攻击
        self.Actions[attack_index + NUM_MOVE]()

        self.time_step += 1

        # print(f"timestep:{self.time_step}, action:{self.MOVE[move_index], self.ATTACK[attack_index]}", end = "")

        raw_state = self._get_state_vector()

        # 更新 mask
        self.action_mask = self._get_action_mask(raw_state)

        # 计算奖励
        reward, done = self._get_reward_done(raw_state, self.prev_state, action)

        # print(f" reward:{reward:.3f}, boss_hp:{raw_state['boss_hp']}, done:{done}")
        if done:
            print(f"time_step:{self.time_step}, boss_hp:{raw_state['boss_hp']}")

        new_frame = self._get_frame()
        image_observation = self._update_stack(new_frame).reshape(IMG_SIZE, IMG_SIZE, 3 * NUM_FRAME)
        vector_observation = self._state_to_observation(raw_state)

        self.prev_state = raw_state


        observation = {
            "image": image_observation,
            "vector": vector_observation
        }

        return observation, reward, done, False, {}
    

    def _get_reward_done(self, state, prev_state, action):
        move_index, attack_index = action

        done = state["player_hp"] <= 0 or state["boss_hp"] <= 0

        reward = 0.0
        reward += player_hp_reward(player_hp=state["player_hp"], prev_player_hp=prev_state["player_hp"])
        reward += boss_hp_reward(boss_hp=state["boss_hp"], prev_boss_hp=prev_state["boss_hp"])

        # reward += souls_reward(attack_index=attack_index, player_souls=state["player_souls"])
        # reward += shadow_dash_reward(attack_index=attack_index, player_shadow_dash_state=state["player_shadow_dash_state"])

        if done:
            reward += done_reward(boss_hp=state["boss_hp"], player_hp=state["player_hp"])

        return reward, done
    