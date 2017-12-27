"""
"""
import hlt
import logging
from collections import defaultdict

targeted_entities = []
targets = defaultdict(None)


def find_nearest_entity(entity, ship, game_map, filters=[]):
    entities = {k: v for k, v in game_map.nearby_entities_by_distance(
        ship).items() if isinstance(v[0], entity)}

    entities_sorted = sorted(zip(entities.keys(), entities.values()))
    for e in entities_sorted:
        entity = e[1][0]
        logging.info(entity)
        needs_skipping = False
        for f in filters:
            needs_skipping = needs_skipping or f(entity)
        if needs_skipping:
            continue
        return entity
    return None


def find_nearest_planet(ship, game_map):
    return find_nearest_entity(hlt.entity.Planet, ship, game_map, [lambda p: p.is_owned()])


def find_new_target(ship, game_map):
    return find_nearest_planet(ship, game_map)


def navigate_to(target, ship, game_map):
    navigate_command = ship.navigate(
        ship.closest_point_to(target),
        game_map,
        speed=int(hlt.constants.MAX_SPEED),
        ignore_ships=False)

    if navigate_command:
        targets[ship] = target
        command_queue.append(navigate_command)


game = hlt.Game("Settler-v3")
logging.info("Starting my Settler bot!")

while True:
    game_map = game.update_map()

    command_queue = []
    for ship in game_map.get_me().all_ships():
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue

        if targets.get(ship) is None:
            targets[ship] = find_new_target(ship, game_map)

        if targets.get(ship) is not None:
            if ship.can_dock(targets[ship]):
                command_queue.append(ship.dock(targets[ship]))
                targets[ship] = None
            else:
                navigate_to(targets[ship], ship, game_map)

    game.send_command_queue(command_queue)
    # TURN END
# GAME END
