"""
"""
import hlt
import logging
from flow_field import FlowField
from command_center import CommandCenter, find_nearest_planet, get_default_direction, is_enemy_or_mine_and_full
from collections import defaultdict


game = hlt.Game("Starfighter-v1")
logging.info("Starting my Starfighter bot!")


def cmd(ship, force):
    logging.info(f'{ship}')
    logging.info(f'{force}')
    logging.info(f'{(force.norm(), force.argument())}')
    return ship.thrust(force.norm(), force.argument())


def default_cmd():
    return (0, 0)


cc = CommandCenter()
commands = defaultdict(default_cmd)
MAX_COMMANDS = 30

while True:
    game_map = game.update_map()
    cc.set_map(game_map)
    field = FlowField(game_map)

    command_queue = []
    cmd_count = 0
    for ship in game_map.get_me().all_ships():
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue

        nearest_planet = find_nearest_planet(ship, game_map)

        if ship.can_dock(nearest_planet.entity) and not is_enemy_or_mine_and_full(nearest_planet.entity, game_map):
            command_queue.append(ship.dock(nearest_planet.entity))
            continue

        if cmd_count < MAX_COMMANDS:
            desired_direction = field.lookup(ship.x, ship.y)
            target = cc.select_target(ship, desired_direction.argument())
            speed, angle = ship.navigate(
                ship.closest_point_to(target.entity),
                game_map,
                speed=int(hlt.constants.MAX_SPEED),
                ignore_ships=False,
                angular_step=3)
            if speed == 0:
                speed = hlt.constants.MAX_SPEED
                angle = desired_direction.argument()
                logging.info(f'going with the gradient {angle}')
            commands[ship.id] = (speed, angle)
            cmd_count += 1
        else:
            speed, angle = commands[ship.id]
            if speed == 0:
                speed = hlt.constants.MAX_SPEED
                angle = get_default_direction(ship, game_map)
                logging.info(f'default direction {angle}')

        command_queue.append(ship.thrust(speed, angle))

    game.send_command_queue(command_queue)
    # TURN END
# GAME END
