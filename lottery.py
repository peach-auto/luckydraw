import random

_sysrandom = random.SystemRandom()


def draw_one(pool, rng=None):
    """从奖池等概率抽一套；rng 仅用于测试时注入固定种子。"""
    if not pool:
        raise ValueError("奖池为空，无法抽奖")
    chooser = rng if rng is not None else _sysrandom
    return chooser.choice(pool)
