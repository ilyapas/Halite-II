"""
"""
import hlt
import logging
from collections import defaultdict
from collections import namedtuple

CLUSTER = 1
nav_count = 0
Target = namedtuple('Target', ['entity', 'distance'])
targeted_entities = defaultdict(int)
targets = defaultdict()

copies = dict()


def is_planet(entity):
    return isinstance(entity, hlt.entity.Planet)


def is_ship(entity):
    return isinstance(entity, hlt.entity.Ship)


def find_nearest_entity(entity, ship, game_map, filters=[]):
    filters.append(lambda e: targeted_entities[e] > CLUSTER)

    entities = {k: v for k, v in game_map.nearby_entities_by_distance(
        ship).items() if isinstance(v[0], entity)}

    entities_sorted = sorted(zip(entities.keys(), entities.values()))
    for e in entities_sorted:
        entity = e[1][0]
        needs_skipping = False
        for f in filters:
            needs_skipping = needs_skipping or f(entity)
        if needs_skipping:
            continue
        return Target(entity, e[0])
    return Target(None, 0)


def find_nearest_planet(ship, game_map, filters=[]):
    return find_nearest_entity(hlt.entity.Planet, ship, game_map, filters)


def find_nearest_ship(ship, game_map, filters=[]):
    return find_nearest_entity(hlt.entity.Ship, ship, game_map, filters)


def find_new_target(ship, game_map):
    target = find_nearest_planet(ship, game_map, [lambda p: p.is_owned()])
    if target.entity is None:
        nearest_enemy_ship = find_nearest_ship(
            ship, game_map, [lambda s: s.owner == game_map.get_me()])
        # nearest_enemy_planet = find_nearest_planet(
        #     ship, game_map, [lambda s: s.owner == game_map.get_me()])
        # if nearest_enemy_planet.distance < nearest_enemy_ship.distance:
        #     target = nearest_enemy_planet
        # else:
        target = nearest_enemy_ship
    return target.entity


def navigate_to(target, ship, game_map):
    navigate_command = ship.navigate(
        ship.closest_point_to(target),
        game_map,
        speed=int(hlt.constants.MAX_SPEED),
        ignore_ships=False)

    if navigate_command:
        global nav_count
        nav_count += 1
        targets[ship.id] = target
        targeted_entities[target] += 1
        command_queue.append(navigate_command)


game = hlt.Game("Settler-v5")
logging.info("Starting my Settler bot!")

while True:
    game_map = game.update_map()

    command_queue = []
    for ship in game_map.get_me().all_ships():
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue

        target = targets.get(ship.id)

        if copies.get(ship.id) is None:
            copies[ship.id] = ship

        if ship.calculate_distance_between(copies[ship.id]) == 0:
            logging.info('Ship stuck')
            target = None

        copies[ship.id] = ship

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
