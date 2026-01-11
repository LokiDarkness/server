import secrets
ICONS = ["bau","cua","tom","ca","ga","nai"]

def roll_dice():
    return [secrets.choice(ICONS) for _ in range(3)]

def calc_reward(bets, dice):
    return sum(dice.count(i) * a for i, a in bets.items())
