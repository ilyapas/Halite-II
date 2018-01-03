"""
"""
import hlt
import logging
import math
from collections import defaultdict
from collections import namedtuple

CLUSTER = 3
TARGET_RECALC = True

nav_count = 0
Target = namedtuple('Target', ['entity', 'distance'])
TargetOption = namedtuple('TargetOption', ['priority', 'squad_size', 'target'])
squads = defaultdict(set)
assignees = defaultdict(set)
targets = defaultdict()
planets_by_size = []
average_radius = 0

copies = dict()


def entity_key(entity):
    return (type(entity), entity.id)


def is_planet(entity):
    return isinstance(entity, hlt.entity.Planet)


def is_ship(entity):
    return isinstance(entity, hlt.entity.Ship)


def is_enemy_or_mine_and_full(planet, game_map):
    if planet.is_owned():
        if planet.owner == game_map.get_me():
            # if len(assignees[entity_key(planet)]) + len(planet.all_docked_ships()) >= planet.num_docking_spots:
            #     return True
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

    options.append(TargetOption(priority=5, squad_size=1, target=find_nearest_planet(
        ship, game_map, [is_enemy_or_mine_and_full])))

    options.append(TargetOption(priority=7, squad_size=1, target=find_nearest_planet(
        ship, game_map, [is_enemy_or_mine_and_full, lambda p, g: p.radius < average_radius])))

    options.append(TargetOption(priority=12, squad_size=1, target=find_nearest_ship(
        ship, game_map, [lambda s, g: s.owner == g.get_me()])))

    nearest_large_enemy_planet = find_nearest_planet(
        ship, game_map, [lambda p, g: p.owner == g.get_me(), lambda p, g: p.radius < average_radius])
    if nearest_large_enemy_planet.entity is not None:
        docked_enemy_ship = find_nearest_ship(
            ship, game_map, [lambda s, g: s.id not in nearest_large_enemy_planet.entity.all_docked_ships()])
        options.append(TargetOption(
            priority=15, squad_size=1, target=docked_enemy_ship))

    nearest_enemy_planet = find_nearest_planet(
        ship, game_map, [lambda p, g: p.owner == g.get_me()])
    if nearest_enemy_planet.entity is not None:
        docked_enemy_ship = find_nearest_ship(
            ship, game_map, [lambda s, g: s.id not in nearest_enemy_planet.entity.all_docked_ships()])
        options.append(TargetOption(
            priority=12, squad_size=1, target=docked_enemy_ship))

    def evaluate_option(opt):
        result = opt.target.distance / opt.priority
        logging.info((result, opt))
        return result

    sorted_options = sorted(options, key=evaluate_option)

    return sorted_options[0]


def navigate_to(target, ship, game_map):
    global assignees
    global targets
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
        assignees[entity_key(target)].add(ship.id)
        logging.info(f'target for ship {ship.id}: {entity_key(target)}')
        logging.info(assignees[entity_key(target)])
        command_queue.append(navigate_command)


game = hlt.Game("Settler-v12")
logging.info("Starting my Settler bot!")
init = True

while True:
    game_map = game.update_map()

    if init:
        planets = [p for p in game_map.all_planets()]
        planets_by_size = list(
            reversed(sorted(planets, key=lambda p: p.radius)))

        rad_list = [p.radius for p in game_map.all_planets()]
        average_radius = sum(rad_list) / len(rad_list)
        init = False

    all_ship_ids = [ship.id for ship in game_map._all_ships()]

    for k in assignees.keys():
        for ship_id in assignees[k].copy():
            if ship_id not in all_ship_ids:
                assignees[k].remove(ship_id)

    command_queue = []
    for ship in game_map.get_me().all_ships():

        if ship.docking_status == ship.DockingStatus.DOCKED:
            if targets.get(ship.id) is not None:
                if ship.id in assignees[entity_key(targets[ship.id])]:
                    logging.info(f'Ship {ship.id} docked')
                    assignees[entity_key(targets[ship.id])].remove(ship.id)
                    targets[ship.id] = None

        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue

        target = targets.get(ship.id)

        if is_ship_stuck(ship):
            target = None

        if target is None or TARGET_RECALC:
            t = find_new_target(ship, game_map)
            if t.target.entity is not None:
                key = entity_key(t.target.entity)
                squads[key].add(ship.id)
                logging.info(squads)
                if len(squads[key]) >= t.squad_size:
                    for s in squads[key]:
                        targets[s] = t.target.entity
                    squads[key].clear()

    for ship in game_map.get_me().all_ships():
        target = targets.get(ship.id)
        if target is not None:
            if is_planet(target):
                if ship.can_dock(target):
                    command_queue.append(ship.dock(target))
                    continue
            navigate_to(target, ship, game_map)

    # logging.info(f'nav_count {nav_count}')
    # logging.info(f'ships_counts {len(game_map.get_me().all_ships())}')
    # logging.info(f'targets {len(targets)}')
    nav_count = 0
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
