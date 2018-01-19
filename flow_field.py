import hlt
import logging
import math
import time
import command_center as cc
from hlt.constants import MAX_SPEED
from vector import Vector


class Force(object):
    def __init__(self, origin, kernel, magnitude):
        self.origin = origin
        self.kernel = kernel
        self.magnitude = magnitude


class FlowField(object):
    def __init__(self, game_map):
        self.game_map = game_map
        self.me = self.game_map.get_me()
        self.planet_forces = self._analyze_planets()
        self.ship_forces = self._analyze_ships()

    def lookup(self, x, y):
        return self.lookup_by_vector(Vector(x, y))

    def lookup_by_vector(self, position):
        force = self._apply_forces(position, self.planet_forces)
        force += self._apply_forces(position, self.ship_forces)
        force += self._apply_border_forces(position)
        return force

    def _apply_forces(self, position, forces):
        sum_forces = Vector()
        for force in forces:
            diff = force.origin - position
            distance = diff.norm()
            gauss = force.magnitude * math.exp(-1 * force.kernel * distance)
            logging.info(f'diff {diff.set_magnitude(gauss)}')
            sum_forces += diff.set_magnitude(gauss)
        logging.info(f'sum {sum_forces}')
        return sum_forces

    def _apply_border_forces(self, position):
        forces = []
        x = Vector(1, 0) * position
        y = Vector(0, 1) * position
        kernel = 0.1
        magnitude = -200
        forces.append(
            Force(Vector(x, 0), kernel, magnitude))
        forces.append(
            Force(Vector(x, self.game_map.height), kernel, magnitude))
        forces.append(
            Force(Vector(0, y), kernel, magnitude))
        forces.append(
            Force(Vector(self.game_map.width, y), kernel, magnitude))
        return self._apply_forces(position, forces)

    def _analyze_planets(self):
        all_planets = self.game_map.all_planets()
        empty_planets = [p for p in all_planets if p.owner is None]
        own_planets = [p for p in all_planets if p.owner is self.me]
        enemy_planets = [p for p in all_planets
                         if p.owner is not self.me and p.owner is not None]

        forces = []
        forces += self._analyze_empty_planets(empty_planets)
        forces += self._analyze_own_planets(own_planets)
        forces += self._analyze_enemy_planets(enemy_planets)
        return forces

    def _analyze_empty_planets(self, planets):
        forces = []
        for planet in planets:
            kernel = 0.1
            magnitude = 200
            forces.append(Force(Vector(planet.x, planet.y), kernel, magnitude))
        return forces

    def _analyze_own_planets(self, planets):
        forces = []
        for planet in planets:
            kernel = 1
            magnitude = 100
            if planet.is_full():
                magnitude = -100
            forces.append(Force(Vector(planet.x, planet.y), kernel, magnitude))
        return forces

    def _analyze_enemy_planets(self, planets):
        forces = []
        for planet in planets:
            kernel = 0.1
            magnitude = 200
            forces.append(Force(Vector(planet.x, planet.y), kernel, magnitude))
        return forces

    def _analyze_ships(self):
        all_ships = self.game_map._all_ships()
        own_ships = [p for p in all_ships if p.owner is self.me]
        enemy_ships = [p for p in all_ships if p.owner is not self.me]

        forces = []
        forces += self._analyze_own_ships(own_ships)
        forces += self._analyze_enemy_ships(enemy_ships)
        return forces

    def _analyze_own_ships(self, ships):
        forces = []
        for ship in ships:
            nearby_own_ships = cc.find_nearby_ships(
                ship, self.game_map, 30, [lambda s, g: s.owner is g.get_me()])
            kernel = 1
            magnitude = -200 + (-0 * len(nearby_own_ships))
            forces.append(Force(Vector(ship.x, ship.y), kernel, magnitude))
        return forces

    def _analyze_enemy_ships(self, ships):
        forces = []
        for ship in ships:
            nearby_enemy_ships = cc.find_nearby_ships(
                ship, self.game_map, 30, [lambda s, g: s.owner is not g.get_me()])
            kernel = 0.1
            magnitude = 100 + (-0 * len(nearby_enemy_ships))
            forces.append(Force(Vector(ship.x, ship.y), kernel, magnitude))
        return forces
