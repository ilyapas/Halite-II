import hlt
import math
from hlt.constants import MAX_SPEED
from vector import Vector


class FlowField(object):
    def __init__(self, game_map):
        self.game_map = game_map
        self.width = game_map.width
        self.height = game_map.height
        self.data = [[Vector(1, 0) for y in range(self.height)]
                     for x in range(self.width)]

    def lookup(self, x, y):
        x = math.floor(x)
        y = math.floor(y)
        return self.data[x][y].set_magnitude(MAX_SPEED)

    def lookup_by_vector(self, position):
        x = Vector(1, 0) * position
        y = Vector(0, 1) * position
        return self.lookup(x, y)
