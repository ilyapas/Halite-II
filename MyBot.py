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
        command_queue.append(cmd(ship, field.lookup(ship.x, ship.y)))

    game.send_command_queue(command_queue)
    # TURN END
# GAME END
