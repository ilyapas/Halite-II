import hlt
import logging
import math
from collections import namedtuple

Target = namedtuple('Target', ['entity', 'distance'])
TargetOption = namedtuple('TargetOption', ['priority', 'squad_size', 'target'])


class CommandCenter(object):
    def __init__(self):
        self.average_radius = 0
        self.game_map = None

    def set_map(self, game_map):
        self.game_map = game_map
        if self.average_radius == 0:
            self.average_radius = calc_average_radius(game_map)

    def select_target(self, ship, desired_angle=None):
        options = []

        options.append(TargetOption(priority=5, squad_size=1, target=find_nearest_planet(
            ship, self.game_map, [is_enemy_or_mine_and_full])))

        options.append(TargetOption(priority=7, squad_size=1, target=find_nearest_planet(
            ship, self.game_map, [is_enemy_or_mine_and_full, lambda p, g: p.radius < self.average_radius])))

        options.append(TargetOption(priority=12, squad_size=1, target=find_nearest_ship(
            ship, self.game_map, [lambda s, g: s.owner == g.get_me()])))

        nearest_large_enemy_planet = find_nearest_planet(
            ship, self.game_map, [lambda p, g: p.owner == g.get_me(), lambda p, g: p.radius < self.average_radius])
        if nearest_large_enemy_planet.entity is not None:
            docked_enemy_ship = find_nearest_ship(
                ship, self.game_map, [lambda s, g: s.id not in nearest_large_enemy_planet.entity.all_docked_ships()])
            options.append(TargetOption(
                priority=15, squad_size=1, target=docked_enemy_ship))

        nearest_enemy_planet = find_nearest_planet(
            ship, self.game_map, [lambda p, g: p.owner == g.get_me()])
        if nearest_enemy_planet.entity is not None:
            docked_enemy_ship = find_nearest_ship(
                ship, self.game_map, [lambda s, g: s.id not in nearest_enemy_planet.entity.all_docked_ships()])
            options.append(TargetOption(
                priority=12, squad_size=1, target=docked_enemy_ship))

        def evaluate_option(opt):
            result = opt.target.distance / opt.priority
            if desired_angle:
                if opt.target.entity is None:
                    return math.inf
                angle = ship.calculate_angle_between(opt.target.entity)
                result *= 1 - math.exp(- 0.001 * (angle - desired_angle)**2)
            logging.info((result, opt))
            return result

        best_option = sorted(options, key=evaluate_option)[0]

        return best_option.target


def calc_average_radius(game_map):
    planets = [p for p in game_map.all_planets()]
    planets_by_size = list(
        reversed(sorted(planets, key=lambda p: p.radius)))

    rad_list = [p.radius for p in game_map.all_planets()]
    return sum(rad_list) / len(rad_list)


def entity_key(entity):
    return (type(entity), entity.id)


def is_planet(entity):
    return isinstance(entity, hlt.entity.Planet)


def is_ship(entity):
    return isinstance(entity, hlt.entity.Ship)


def is_enemy_or_mine_and_full(planet, game_map):
    if planet.is_owned():
        if planet.owner == game_map.get_me():
            if planet.is_full():
                return True
        else:
            return True
    return False


def empty_planet_ratio(game_map):
    empty_planets = [p for p in game_map.all_planets() if not p.is_owned()]
    return 1 + (len(empty_planets) / len(game_map.all_planets()))


def find_nearest_entity(entity, ship, game_map, filters=[]):
    entities = {k: v for k, v in game_map.nearby_entities_by_distance(
        ship).items() if isinstance(v[0], entity)}

    entities_sorted = sorted(zip(entities.keys(), entities.values()))
    for e in entities_sorted:
        entity = e[1][0]
        needs_skipping = False
        for f in filters:
            needs_skipping = needs_skipping or f(entity, game_map)
        if needs_skipping:
            continue
        return Target(entity, e[0])
    return Target(None, math.inf)


def find_nearby_entities(entity, target, game_map, radius, filters=[]):
    entities = [v for k, v in game_map.nearby_entities_by_distance(
        target).items() if isinstance(v[0], entity) if k < radius]
    filtered_entities = []
    for e in entities:
        needs_skipping = False
        for f in filters:
            needs_skipping = needs_skipping or f(e[0], game_map)
        if needs_skipping:
            continue
        filtered_entities.append(e[0])
    return filtered_entities


def find_nearest_planet(ship, game_map, filters=[]):
    return find_nearest_entity(hlt.entity.Planet, ship, game_map, filters)


def find_nearest_ship(ship, game_map, filters=[]):
    return find_nearest_entity(hlt.entity.Ship, ship, game_map, filters)


def find_nearby_ships(target, game_map, radius, filters=[]):
    return find_nearby_entities(hlt.entity.Ship, target, game_map, radius, filters)


def get_default_direction(ship, game_map):
    enemy_ships = [s for s in game_map._all_ships()
                   if s.owner is not game_map.get_me()]
    average_position_x = sum([s.x for s in enemy_ships]) / len(enemy_ships)
    average_position_y = sum([s.y for s in enemy_ships]) / len(enemy_ships)
    return ship.calculate_angle_between(hlt.entity.Position(average_position_x, average_position_y))
