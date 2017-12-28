"""
"""
import hlt
import logging
import math
from collections import defaultdict
from collections import namedtuple

CLUSTER = 3
nav_count = 0
Target = namedtuple('Target', ['entity', 'distance'])
TargetOption = namedtuple('TargetOption', ['priority', 'target'])
targeted_entities = defaultdict(int)
targets = defaultdict()

copies = dict()


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


def is_ship_stuck(ship):
    if copies.get(ship.id) is None:
        copies[ship.id] = ship

    result = False
    if ship.calculate_distance_between(copies[ship.id]) == 0:
        result = True

    copies[ship.id] = ship
    return result


def find_nearest_entity(entity, ship, game_map, filters=[]):
    filters.append(lambda e, g: targeted_entities[e] > CLUSTER)

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


def find_nearest_planet(ship, game_map, filters=[]):
    return find_nearest_entity(hlt.entity.Planet, ship, game_map, filters)


def find_nearest_ship(ship, game_map, filters=[]):
    return find_nearest_entity(hlt.entity.Ship, ship, game_map, filters)


def find_new_target(ship, game_map):
    options = []

    options.append(TargetOption(5, find_nearest_planet(
        ship, game_map, [is_enemy_or_mine_and_full])))

    options.append(TargetOption(3, find_nearest_ship(
        ship, game_map, [lambda s, g: s.owner == g.get_me()])))

    sorted_options = sorted(
        options, key=lambda opt: opt.target.distance / opt.priority)

    target = sorted_options[0].target
    return target.entity


def navigate_to(target, ship, game_map):
    navigate_command = ship.navigate(
        ship.closest_point_to(target),
        game_map,
        speed=int(hlt.constants.MAX_SPEED),
        ignore_ships=False,
        angular_step=3)

    if navigate_command:
        global nav_count
        nav_count += 1
        targets[ship.id] = target
        targeted_entities[target] += 1
        command_queue.append(navigate_command)


game = hlt.Game("Settler-v8")
logging.info("Starting my Settler bot!")

while True:
    game_map = game.update_map()

    command_queue = []
    for ship in game_map.get_me().all_ships():
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue

        target = targets.get(ship.id)

        if is_ship_stuck(ship):
            target = None

        if target is None:
            target = find_new_target(ship, game_map)
            new_target = True

        if target is not None:
            if is_planet(target):
                if ship.can_dock(target):
                    command_queue.append(ship.dock(target))
                    targets[ship.id] = None
                    continue
            if new_target:
                navigate_to(target, ship, game_map)
        targets[ship.id] = target

    logging.info(f'nav_count {nav_count}')
    logging.info(f'ships_counts {len(game_map.get_me().all_ships())}')
    logging.info(f'targets {len(targets)}')
    nav_count = 0
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
