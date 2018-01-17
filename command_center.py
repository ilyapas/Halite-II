import hlt
import logging
import math
from collections import namedtuple

Target = namedtuple('Target', ['entity', 'distance'])


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
