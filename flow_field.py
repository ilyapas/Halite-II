import hlt
from vector import Vector


class FlowField(object):
    def __init__(self, game_map):
        self.game_map = game_map
        self.data = [[Vector(1, 0) for x in range(self.game_map.width)]
                     for y in range(self.game_map.height)]

    def lookup(self, position):
        x = int(Vector(1, 0) * position)
        y = int(Vector(0, 1) * position)
        return self.data[x][y]
