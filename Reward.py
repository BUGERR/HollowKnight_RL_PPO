
# 游戏数值和奖励分数的比例
PLAYER_HP_REWARD_RATIO = 1
BOSS_HP_REWARD_RATIO = 0.03

BOSS_MAX_HP = 900
PLAYER_MAX_HP = 9

# SHADOW_DASH_STATE = 1  # 黑冲状态
# NORMAL_DASH_STATE = 0  # 普通状态

# ATTACK_SPACE = [
#             "Attack_Down", "Mid_Jump_Attack",
#             "Attack", "Attack_Up", 
#             "Dash", 
#             "Skill", "Skill_Down", "Skill_Up"
#             ]

# DASH = ATTACK_SPACE.index("Dash")
# SKILL = ATTACK_SPACE.index("Skill")
# SKILL_DOWN = ATTACK_SPACE.index("Skill_Down")
# SKILL_UP = ATTACK_SPACE.index("Skill_Up")


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


def done_reward(boss_hp, player_hp):
    if boss_hp <= 0:
        return PLAYER_MAX_HP * PLAYER_HP_REWARD_RATIO # 整个一轮里，如果赢了，就补上扣血的惩罚，相当于奖励都来自boss血量

    else:
        return - BOSS_MAX_HP * BOSS_HP_REWARD_RATIO  # 整个一轮，如果输了，一共惩罚玩家掉血，加上剩余boss血量
    return 0

# def souls_reward(attack_index, player_souls):
#     if attack_index in [SKILL, SKILL_DOWN, SKILL_UP] and player_souls < SKILL_SOULS_COST:
#         return -1 *  PLAYER_HP_REWARD_RATIO # 灵魂不足，惩罚，相当于自己掉血
#     return 0  # 灵魂足够，不惩罚


# def shadow_dash_reward(attack_index, player_shadow_dash_state):
#     if attack_index == DASH and player_shadow_dash_state == SHADOW_DASH_STATE:
#         return 0
#     elif attack_index == DASH and player_shadow_dash_state == NORMAL_DASH_STATE:
#         return -1 * PLAYER_HP_REWARD_RATIO
#     return 0