"""
"""
import hlt
import logging
from collections import defaultdict

targeted_planets = []
targets = defaultdict(None)


def find_new_target(ship, game_map):
    planets = {k: v for k, v in game_map.nearby_entities_by_distance(
        ship).items() if isinstance(v[0], hlt.entity.Planet)}

    planets_sorted = sorted(zip(planets.keys(), planets.values()))
    for p in planets_sorted:
        planet = p[1][0]
        logging.info(planet)
        if planet.is_owned():
            continue
        return planet
    return None


def navigate_to(target, ship, game_map):
    navigate_command = ship.navigate(
        ship.closest_point_to(target),
        game_map,
        speed=int(hlt.constants.MAX_SPEED),
        ignore_ships=False)

    if navigate_command:
        targets[ship] = target
        command_queue.append(navigate_command)


game = hlt.Game("Settler-v2")
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
