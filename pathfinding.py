import hlt
import logging
import math
from hlt.entity import Entity, Ship, Planet, Position


def navigate(ship, target, game_map, speed, avoid_obstacles=True, max_corrections=90, angular_step=1,
             ignore_ships=False, ignore_planets=False):
    """
    Move a ship to a specific target position (Entity). It is recommended to place the position
    itself here, else navigate will crash into the target. If avoid_obstacles is set to True (default)
    will avoid obstacles on the way, with up to max_corrections corrections. Note that each correction accounts
    for angular_step degrees difference, meaning that the algorithm will naively try max_correction degrees before giving
    up (and returning None). The navigation will only consist of up to one command; call this method again
    in the next turn to continue navigating to the position.

    :param Entity target: The entity to which you will navigate
    :param game_map.Map game_map: The map of the game, from which obstacles will be extracted
    :param int speed: The (max) speed to navigate. If the obstacle is nearer, will adjust accordingly.
    :param bool avoid_obstacles: Whether to avoid the obstacles in the way (simple pathfinding).
    :param int max_corrections: The maximum number of degrees to deviate per turn while trying to pathfind. If exceeded returns None.
    :param int angular_step: The degree difference to deviate if the original destination has obstacles
    :param bool ignore_ships: Whether to ignore ships in calculations (this will make your movement faster, but more precarious)
    :param bool ignore_planets: Whether to ignore planets in calculations (useful if you want to crash onto planets)
    :return string: The command trying to be passed to the Halite engine or None if movement is not possible within max_corrections degrees.
    :rtype: str
    """
    # Assumes a position, not planet (as it would go to the center of the planet otherwise)
    if max_corrections <= 0:
        return 0, 0
    distance = ship.calculate_distance_between(target)
    angle = ship.calculate_angle_between(target)
    ignore = () if not (ignore_ships or ignore_planets) \
        else Ship if (ignore_ships and not ignore_planets) \
        else Planet if (ignore_planets and not ignore_ships) \
        else Entity
    if avoid_obstacles and game_map.obstacles_between(ship, target, ignore):
        new_target_dx = math.cos(math.radians(
            angle + angular_step)) * distance
        new_target_dy = math.sin(math.radians(
            angle + angular_step)) * distance
        new_target = Position(ship.x + new_target_dx,
                              ship.y + new_target_dy)
        return ship.navigate(new_target, game_map, speed, True, max_corrections - 1, angular_step)
    speed = speed if (distance >= speed) else distance
    return speed, angle
