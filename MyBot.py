"""
"""
import hlt
import logging
import math
import pathfinding
from collections import defaultdict
from collections import namedtuple
from flow_field import FlowField

CLUSTER = 3
TARGET_RECALC = True
RUSH_THRESHOLD = 2.5
FLEE_THRESHOLD = 0.3

init = True
rush = 0
flee = math.inf
planet_bonus = 0
nav_count = 0
last_target = None
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


def find_new_target(ship, game_map, desired_angle=None):
    options = []

    options.append(TargetOption(priority=5 + planet_bonus, squad_size=1, target=find_nearest_planet(
        ship, game_map, [is_enemy_or_mine_and_full])))

    options.append(TargetOption(priority=7 + planet_bonus, squad_size=1, target=find_nearest_planet(
        ship, game_map, [is_enemy_or_mine_and_full, lambda p, g: p.radius < average_radius])))

    nearest_enemy_ship = find_nearest_ship(
        ship, game_map, [lambda s, g: s.owner == g.get_me()])
    options.append(TargetOption(priority=12 + rush * 200,
                                squad_size=1, target=nearest_enemy_ship))

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

    pos_x = ship.x - 2 * (nearest_enemy_ship.entity.x - ship.x)
    pos_y = ship.y - 2 * (nearest_enemy_ship.entity.y - ship.y)
    if pos_x < 10 or pos_x > game_map.width - 10:
        pos_x = ship.x
    if pos_y < 10 or pos_y > game_map.height - 10:
        pos_y = ship.y
    fleeing_direction = hlt.entity.Position(pos_x, pos_y)
    fleeing_target = Target(fleeing_direction, flee)
    options.append(TargetOption(
        priority=1000, squad_size=1, target=fleeing_target))

    global last_target
    global init

    def evaluate_option(opt):
        distance = opt.target.distance
        logging.info(f'last target {last_target}')
        logging.info(f'opt.target.entity {opt.target.entity}')
        if init and last_target and opt.target.entity:
            if opt.target.entity.id == last_target:
                distance = math.inf

        result = distance / opt.priority
        if desired_angle:
            if opt.target.entity is None:
                return math.inf
            angle = ship.calculate_angle_between(opt.target.entity)
            result *= 1 - math.exp(-0.1 * (angle - desired_angle)**2)
        logging.info((result, opt))
        return result

    sorted_options = sorted(options, key=evaluate_option)
    last_target = sorted_options[0].target.entity.id
    return sorted_options[0]


def navigate_to(target, ship, game_map):
    global assignees
    global targets
    navigate_command = pathfinding.navigate(ship,
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
        command_queue.append(ship.thrust(
            navigate_command[0], navigate_command[1]))


def rush_feasable(game_map):
    if len(game_map.all_players()) > 2:
        return False

    my_ship = game_map.get_me().all_ships()[0]
    enemy_ship = find_nearest_ship(
        my_ship, game_map, [lambda s, g: s.owner == g.get_me()]).entity
    nearest_planet_for_enemy = find_nearest_planet(enemy_ship, game_map).entity

    distance_to_enemy = my_ship.calculate_distance_between(enemy_ship)
    enemy_distance_to_planet = enemy_ship.calculate_distance_between(
        nearest_planet_for_enemy)
    go_go_go = (distance_to_enemy / enemy_distance_to_planet) < RUSH_THRESHOLD
    logging.info(
        f'RUSH: distance_to_enemy {distance_to_enemy} enemy_distance_to_planet {enemy_distance_to_planet}')
    if go_go_go:
        logging.info("GO GO GO!!!")
    return go_go_go


def fleeing_feasable(game_map):
    if len(game_map.all_players()) < 4:
        return False

    if len([p for p in game_map.all_planets() if not p.is_owned()]) > 1:
        return False

    num_own_planets = len(
        [p for p in game_map.all_planets() if p.owner == game_map.get_me()])
    num_planets_stats = []
    for player in game_map.all_players():
        num_planets_stats.append(
            len([p for p in game_map.all_planets() if p.owner == player]))
    max_num_planents = max(num_planets_stats) + 1
    ruuuun = (num_own_planets / max_num_planents) < FLEE_THRESHOLD
    logging.info(
        f'FLEE: num_own_planets {num_own_planets} max_num_planents {max_num_planents}')
    if ruuuun:
        logging.info("RUUUUN!!!")
    return ruuuun


game = hlt.Game("Settler-v14")
logging.info("Starting my Settler bot!")

while True:
    game_map = game.update_map()
    # field = FlowField(game_map)

    if init:
        planets = [p for p in game_map.all_planets()]
        planets_by_size = list(
            reversed(sorted(planets, key=lambda p: p.radius)))

        rad_list = [p.radius for p in game_map.all_planets()]
        average_radius = sum(rad_list) / len(rad_list)

        if rush_feasable(game_map):
            rush = 1

        if len(game_map.all_players()) > 2:
            planet_bonus = 12

    if fleeing_feasable(game_map):
        flee = 1

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
            # desired_direction = field.lookup(ship.x, ship.y)
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
    init = False
    # TURN END
# GAME END
