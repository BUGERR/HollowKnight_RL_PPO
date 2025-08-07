
# 游戏数值和奖励分数的比例
PLAYER_HP_REWARD_RATIO = 1.0
BOSS_HP_REWARD_RATIO = 0.03

BOSS_MAX_HP = 900
PLAYER_MAX_HP = 9



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



        