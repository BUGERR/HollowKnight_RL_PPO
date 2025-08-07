
# 游戏数值和奖励分数的比例
PLAYER_HP_REWARD_RATIO = 1.2
BOSS_HP_REWARD_RATIO = 0.04

DIRECTION_REWARD_RATIO = 0.5

BOSS_MAX_HP = 900
PLAYER_MAX_HP = 9

DANGER_RANGE = 2.5

PLAYER_ATTACK_RANGE = 4.8

DASH_DIS = 5.6


MOVE_SPACE = [ 
            "Move_Left", "Move_Right", 
            "Turn_Left","Turn_Right"
                    ]
MOVE_LEFT = MOVE_SPACE.index("Move_Left")
TURN_LEFT = MOVE_SPACE.index("Turn_Left")
MOVE_RIGHT = MOVE_SPACE.index("Move_Right")
TURN_RIGHT = MOVE_SPACE.index("Turn_Right")

ATTACK_SPACE = [
            "Attack_Down", "Mid_Jump_Attack",
            "Attack", 
            # "Attack_Up", 
            "Dash", 
            # "Skill", 
            "Skill_Down", 
            # "Skill_Up"
            ]

DASH = ATTACK_SPACE.index("Dash")


# 玩家血量奖励，掉血就惩罚，否则无（因为没让它学回血，鼓励躲技能）
def player_hp_reward(player_hp, prev_player_hp):
    player_hp_increase = player_hp - prev_player_hp
    if player_hp_increase < 0:
        return PLAYER_HP_REWARD_RATIO * player_hp_increase
    return 0


# boss 血量奖励，鼓励让 boss 掉血
def boss_hp_reward(boss_hp, prev_boss_hp):
    boss_hp_reduce = prev_boss_hp - boss_hp
    if boss_hp_reduce > 0:
        return boss_hp_reduce * BOSS_HP_REWARD_RATIO
    return 0


def done_reward(player_hp, boss_hp):
    if boss_hp <= 0:
        return (player_hp + PLAYER_MAX_HP) * PLAYER_HP_REWARD_RATIO  # 整个一轮里，如果赢了，就补上扣血的惩罚，相当于奖励都来自boss血量

    else:
        return - BOSS_MAX_HP * BOSS_HP_REWARD_RATIO  # 整个一轮，如果输了，惩罚剩余boss血量
    return 0


def dash_reward(move_index, attack_index, player_x, boss_x):
    reward = 0
    if attack_index == DASH:
        if player_x - boss_x > 0: # boss 在玩家左边
            if move_index in [MOVE_LEFT, TURN_LEFT] and DASH_DIS - 1 < abs(player_x - boss_x) < DASH_DIS + 1:
                reward -= 1
        else: # boss 在玩家右边
            if move_index in [MOVE_RIGHT, TURN_RIGHT] and DASH_DIS - 1 < abs(player_x - boss_x) < DASH_DIS + 1:
                reward -= 1
    return reward


# 控制玩家朝向，鼓励在安全距离时面向 boss，要和 boss 重合时惩罚面向
def move_direction_reward(move_index, player_x, boss_x):

    # 如果玩家朝向 是 boss 所在方向，这时根据是否危险距离来奖励或惩罚
    # 如果不同向，且危险距离，正好拉开， > 0 是奖励

    player_facing, boss_side, overlap = 0, 0, 0 # -1 是左，1是右。只要判断是同向就行

    if player_x - boss_x > 0: # boss 在玩家左边
        boss_side = -1
    else:
        boss_side = 1

    if move_index == MOVE_LEFT or move_index == TURN_LEFT: # 玩家面向左
        player_facing = -1
    else:
        player_facing = 1

    if abs(player_x - boss_x) < DANGER_RANGE: # 危险距离，惩罚重合
        overlap = -1
    else:
        overlap = 1

    return player_facing * boss_side * overlap * DIRECTION_REWARD_RATIO



# 避免过近，还要鼓励靠近，保持在能攻击到 boss 的距离
def move_range_reward(player_x, boss_x):

    player_boss_range = abs(player_x - boss_x)

    # 不要离 boss 太近
    if player_boss_range < DANGER_RANGE:
        return -1
    
    # 还要保持 boss 在攻击范围内
    elif player_boss_range < PLAYER_ATTACK_RANGE:
        return 1
    
    return 0
    
    # # 如果超出玩家攻击范围，鼓励用移动靠近 boss
    # else:
    #     if move_index < TURN_LEFT:
    #         return 2
    #     else:
    #         return -2
        