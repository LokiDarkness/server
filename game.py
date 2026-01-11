import secrets

ICONS = ["bau", "cua", "tom", "ca", "ga", "nai"]

def roll_dice():
    return [secrets.choice(ICONS) for _ in range(3)]

def calc_reward(bets, dice):
    reward = 0
    for icon, amount in bets.items():
        reward += dice.count(icon) * amount
    return reward
