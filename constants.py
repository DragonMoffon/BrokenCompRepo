import arcade

import time

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()


# ---- HELPER FUNCTIONS ---- #
def expand(x, factor=1):
    return (x + 1) * factor / 2


def expand2d(x, y, factor=1):
    return (x + 1) * factor * SCREEN_WIDTH / 2, (y+1) * factor * SCREEN_HEIGHT


def shrink(x, factor):
    return 2 * x / factor - 1


def shrink2d(x, y, factor=1):
    return 2*x/(factor*SCREEN_WIDTH) - 1, 2*y/(factor*SCREEN_HEIGHT) - 1


def clamp(x, minx, maxx):
    return min(max(x, minx), maxx)


def mix(x, y, a):
    return x * (1-a) + y * a


def neg_inf_floor(x):
    return int(x) if x > 0 else int(x)-1
