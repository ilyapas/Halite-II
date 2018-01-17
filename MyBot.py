"""
"""
import hlt
import logging
import command_center as cc
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

        nearest_planet = cc.find_nearest_planet(ship, game_map)

        if ship.can_dock(nearest_planet.entity) and not nearest_planet.entity.is_full():
            command_queue.append(ship.dock(nearest_planet.entity))
            continue

        if nearest_planet.distance < 20:
            speed = 5
        else:
            speed = hlt.constants.MAX_SPEED

        command_queue.append(cmd(ship, field.lookup(
            ship.x, ship.y).set_magnitude(speed)))

    game.send_command_queue(command_queue)
    # TURN END
# GAME END
