"""
"""
import hlt
import logging
from flow_field import FlowField
from command_center import CommandCenter, find_nearest_planet

game = hlt.Game("Starfighter-v1")
logging.info("Starting my Starfighter bot!")


def cmd(ship, force):
    logging.info(f'{ship}')
    logging.info(f'{force}')
    logging.info(f'{(force.norm(), force.argument())}')
    return ship.thrust(force.norm(), force.argument())


cc = CommandCenter()
while True:
    game_map = game.update_map()
    cc.set_map(game_map)
    field = FlowField(game_map)

    command_queue = []
    for ship in game_map.get_me().all_ships():
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue

        nearest_planet = find_nearest_planet(ship, game_map)

        if ship.can_dock(nearest_planet.entity) and not nearest_planet.entity.is_full():
            command_queue.append(ship.dock(nearest_planet.entity))
            continue

        desired_direction = field.lookup(ship.x, ship.y)
        target = cc.select_target(ship, desired_direction.argument())
        speed, angle = ship.navigate(
            ship.closest_point_to(target.entity),
            game_map,
            speed=int(hlt.constants.MAX_SPEED),
            ignore_ships=False,
            angular_step=3)

        command_queue.append(ship.thrust(speed, angle))

    game.send_command_queue(command_queue)
    # TURN END
# GAME END
