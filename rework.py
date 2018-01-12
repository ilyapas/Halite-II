"""
"""
import hlt
import logging
from starfighter import Starfighter
from command_center import CommandCenter
from collections import defaultdict

game = hlt.Game("Starfighter-v1")
logging.info("Starting my Starfighter bot!")


def cmd(ship, force):
    logging.info(f'{ship}')
    logging.info(f'{force}')
    logging.info(f'{(force.norm(), force.argument())}')
    return ship.thrust(force.norm(), force.argument())


fighters = defaultdict(Starfighter)
cc = CommandCenter()
while True:
    game_map = game.update_map()
    cc.set_map(game_map)

    command_queue = []
    for ship in game_map.get_me().all_ships():
        fighter = fighters[ship.id]
        fighter.set_position(ship.x, ship.y)

    for ship in game_map.get_me().all_ships():
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue

        target = cc.select_target(ship)
        fighter = fighters[ship.id]

        if ship.can_dock(target.entity):
            command_queue.append(ship.dock(target.entity))
            continue

        speed, angle = ship.navigate(
            ship.closest_point_to(target.entity),
            game_map,
            speed=int(hlt.constants.MAX_SPEED),
            ignore_ships=False,
            angular_step=3)
        fighter.set_velocity(speed, angle)
        other_fighters_position = [fighters[k]
                                   for k in fighters.keys() if k != ship.id]
        fighter.update(other_fighters_position)
        command_queue.append(cmd(ship, fighter.velocity))

    game.send_command_queue(command_queue)
    logging.info(fighters)
    # TURN END
# GAME END
