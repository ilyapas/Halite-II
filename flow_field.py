import hlt
import logging
import math
import time
from hlt.constants import MAX_SPEED
from vector import Vector


class Force(object):
    def __init__(self, origin, kernel, magnitude):
        self.origin = origin
        self.kernel = kernel
        self.magnitude = magnitude


class FlowField(object):
    def __init__(self, game_map, scale):
        self.game_map = game_map
        self.planet_forces = self._analyze_planets()
        self.ship_forces = self._analyze_ships()

    def lookup(self, x, y):
        return self.lookup_by_vector(Vector(x, y))

    def lookup_by_vector(self, position):
        force = self._apply_forces(position, self.planet_forces)
        force = self._apply_forces(position, self.ship_forces)
        return force

    def _apply_forces(self, position, forces):
        sum_forces = Vector()
        for force in forces:
            diff = force.origin - position
            distance = diff.norm()
            gauss = force.magnitude * math.exp(-1 * force.kernel * distance)
            logging.info(f'diff {diff.set_magnitude(gauss)}')
            sum_forces += diff.set_magnitude(gauss)
        sum_forces = sum_forces.set_magnitude(MAX_SPEED - 1)
        logging.info(f'sum {sum_forces}')
        return sum_forces

    def _analyze_planets(self):
        me = self.game_map.get_me()
        all_planets = self.game_map.all_planets()
        empty_planets = [p for p in all_planets if p.owner is None]
        own_planets = [p for p in all_planets if p.owner is me]
        enemy_planets = [p for p in all_planets if p.owner is not me]

        forces = []
        forces += self._analyze_empty_planets(empty_planets)
        forces += self._analyze_own_planets(own_planets)
        forces += self._analyze_enemy_planets(enemy_planets)
        return forces

    def _analyze_empty_planets(self, planets):
        forces = []
        for planet in planets:
            forces.append(Force(Vector(planet.x, planet.y), 0.0001, 1000.0))
        return forces

    def _analyze_own_planets(self, planets):
        return list()

    def _analyze_enemy_planets(self, planets):
        forces = []
        for planet in planets:
            forces.append(Force(Vector(planet.x, planet.y), 0.0001, -1000.0))
        return forces

    def _analyze_ships(self):
        me = self.game_map.get_me()
        all_ships = self.game_map._all_ships()
        own_ships = [p for p in all_ships if p.owner is me]
        enemy_ships = [p for p in all_ships if p.owner is not me]

        forces = []
        forces += self._analyze_own_ships(own_ships)
        forces += self._analyze_enemy_ships(enemy_ships)
        return forces

    def _analyze_own_ships(self, ships):
        forces = []
        for ship in ships:
            forces.append(Force(Vector(ship.x, ship.y), 0.00001, -100.0))
        return forces

    def _analyze_enemy_ships(self, ships):
        forces = []
        for ship in ships:
            forces.append(Force(Vector(ship.x, ship.y), 0.0001, 1000.0))
        return forces
