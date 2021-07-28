import random
import time
import math
from math import sqrt

from constants import *
from vector import Vec2d

# ---- CONSTANTS ---- #
GRADIANT_PERMUTATIONS = (Vec2d(1, 0), Vec2d(sqrt(3)/2, 0.5), Vec2d(sqrt(2)/2, sqrt(2)/2), Vec2d(0.5, sqrt(3)/2),
                         Vec2d(0, 1), Vec2d(-0.5, sqrt(3)/2), Vec2d(-sqrt(2)/2, sqrt(2)/2), Vec2d(-sqrt(3)/2, 0.5),
                         Vec2d(-1, 0), Vec2d(-sqrt(3)/2, -0.5), Vec2d(-sqrt(2)/2, -sqrt(2)/2), Vec2d(-0.5, -sqrt(3)/2),
                         Vec2d(0, -1), Vec2d(0.5, -sqrt(3)/2), Vec2d(sqrt(2/2), -sqrt(2)/2), Vec2d(sqrt(3)/2, -0.5))

PERLIN_SEED = (time.time() % 1) * int(time.time())

# ---- HELPER FUNCTIONS ---- #


# ---- PERLIN DATA CLASSES ---- #
class PerlinTree:

    def __init__(self, seed=1, depth=8):
        self.seed = math.sin(time.time()*765*seed)/math.tan(time.time()*32*seed) % 1 + 1
        self.depth = depth
        self._octaves = {i: {} for i in range(depth)}

    def find_gradient(self, depth, point):
        if depth <= self.depth:
            octave = self._octaves[depth]
            seed = (sqrt(PERLIN_SEED**depth)*sum(point)/(point[0] if point[0] else 1))/self.seed
            random.seed(seed)
            gradiant = random.choice(GRADIANT_PERMUTATIONS)
            octave[point] = gradiant
            return gradiant
        return 0, 1

    def __getitem__(self, args):
        """
        :param args: ALl the points to be found and the index 0 is the depth
        :return: A list of Vec2d that are of 8 specific rotations.
        """
        depth = args[0]
        if depth <= self.depth:
            octave = self._octaves[depth]
            return tuple(octave.get(arg, self.find_gradient(depth, arg)) for arg in args[1:])


def simplex_perlin_2d(perlin_tree: PerlinTree, depth: int, x: float, y: float):
    """
    A python implementation of simplex perlin noise. definitely not efficient, but good enough
    :param perlin_tree: The randomly chosen perlin vectors in a easy to read map.
    :param depth: the "Octave" of the perlin noise.
    :param x: the floating point x coord of the point.
    :param y: the floating point y coord of the point.
    :return: a value between 0 and 1.
    """

    # Skew to find our simplex coord
    skew_factor = 0.5*(sqrt(3.0)-1)
    skew = (x + y) * skew_factor
    i = neg_inf_floor(x+skew)
    j = neg_inf_floor(y+skew)

    unskew_factor = (3.0 - sqrt(3.0))/6.0
    unskew = (i + j) * unskew_factor
    x_int = i-unskew
    y_int = j-unskew
    x0 = x-x_int
    y0 = y-y_int

    i1, j1 = (1, 0) if x0 > y0 else (0, 1)

    x1 = x0 - i1 + unskew_factor
    y1 = y0 - j1 + unskew_factor
    x2 = x0 - 1.0 + 2.0 * unskew_factor
    y2 = y0 - 1.0 + 2.0 * unskew_factor

    point0, point1, point2 = perlin_tree[depth, (x0, y0), (x1, y1), (x2, y2)]
    # noise contribution
    t0 = 1 - x0**2 - y0**2
    print(t0)
    if t0 < 0:
        n0 = 0
    else:
        t0 *= t0
        n0 = t0 * t0 * point0.dot(Vec2d(x0, y0))

    t1 = 1 - x1**2 - y**2
    print(t1)
    if t1 < 0:
        n1 = 0
    else:
        t1 *= t1
        n1 = t1 * t1 * point1.dot(Vec2d(x1, y1))

    t2 = 1 - x2**2 - y**2
    print(t2)
    if t2 < 0:
        n2 = 0
    else:
        t2 *= t2
        n2 = t2 * t2 * point2.dot(Vec2d(x2, y2))

    return 70 * (n0 + n1 + n2)


def original_perlin_2d(perlin_tree: PerlinTree, depth: int, x: float, y: float):
    int_x = neg_inf_floor(x)
    int_y = neg_inf_floor(y)
    fract_x = x % 1
    fract_y = y % 1
    fract_pos = Vec2d(fract_x, fract_y)
    print("pos", fract_pos)
    corner_sw, corner_nw, corner_ne, corner_se = perlin_tree[depth,
                                                             (int_x, int_y), (int_x, int_y+1),
                                                             (int_x+1, int_y+1), (int_x+1, int_y)]

    print("corners:", corner_sw, corner_nw, corner_ne, corner_se)

    function = fract_pos * fract_pos * fract_pos * (fract_pos*(fract_pos*6-15)+10)
    print("function", function)
    print("function breakdown", fract_pos*fract_pos*fract_pos, (fract_pos*(fract_pos*6-15)+10))

    north_mix = mix(corner_nw.dot(fract_pos-Vec2d(0, 1)), corner_ne.dot(fract_pos-Vec2d(1, 1)), function.x)
    print("north:", north_mix)
    south_mix = mix(corner_sw.dot(fract_pos-Vec2d(0, 0)), corner_se.dot(fract_pos-Vec2d(1, 0)), function.x)
    print("south", south_mix)
    vertical_mix = mix(south_mix, north_mix, function.y)
    print("mix", vertical_mix)
    return vertical_mix
