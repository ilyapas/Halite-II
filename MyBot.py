"""
"""
import hlt
import logging
from flow_field import FlowField

game = hlt.Game("Starfighter-v1")
logging.info("Starting my Starfighter bot!")


def cmd(ship, force):
    logging.info(f'{ship}')
    logging.info(f'{force}')
    logging.info(f'{(force.norm(), force.argument())}')
    return ship.thrust(force.norm(), force.argument())


while True:
    game_map = game.update_map()
    field = FlowField(game_map)

    command_queue = []
    for ship in game_map.get_me().all_ships():
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue

        planets = {k: v for k, v in game_map.nearby_entities_by_distance(ship).items()
                   if isinstance(v[0], hlt.entity.Planet)}
        nearest_planet = sorted(zip(planets.keys(), planets.values()))[0][1][0]

        if ship.can_dock(nearest_planet) and not nearest_planet.is_full():
            command_queue.append(ship.dock(nearest_planet))
            continue

        command_queue.append(cmd(ship, field.lookup(ship.x, ship.y)))

    game.send_command_queue(command_queue)
    # TURN END
# GAME END
