from vector import Vector
from hlt.constants import MAX_SPEED
import logging


class Starfighter(object):
    def __init__(self):
        self.position = Vector()
        self.velocity = Vector()
        self.acceleration = Vector()
        self.target = Vector()

    def __repr__(self):
        return f'Fighter: position {self.position}, velocity {self.velocity}'

    def set_position(self, x, y):
        self.position = Vector(x, y)

    def set_target(self, x, y):
        self.target = Vector(x, y)
        dist = (self.target - self.position).norm()
        if dist > 10:
            self.flocking = 0.3
        else:
            self.flocking = 0

    def set_velocity(self, speed, angle):
        self.velocity = Vector.from_polar(speed, angle)

    def update(self, other_fighters, obstacles=[]):

        logging.info(f'Me {self}')
        logging.info(f'Others {other_fighters}')

        # self.apply_force(self.arrive(self.target))
        self.apply_force(self.flock(other_fighters) * self.flocking)
        self.apply_force(self.avoid(obstacles) * 0.5)

        self.velocity += self.acceleration
        self.velocity = self.velocity.limit(MAX_SPEED)
        self.acceleration *= 0
        logging.info(f'Velocity {self.velocity}')

    def apply_force(self, force):
        self.acceleration += force

    def seek(self, target):
        desired = target - self.position
        desired = desired.set_magnitude(MAX_SPEED)
        steer = desired - self.velocity
        steer = steer.limit(MAX_SPEED)
        return steer

    def arrive(self, target):
        slow_down_zone = 10
        desired = target - self.position
        dist = desired.norm()
        if dist < slow_down_zone:
            desired = desired.set_magnitude(MAX_SPEED * dist / slow_down_zone)
        else:
            desired = desired.set_magnitude(MAX_SPEED)
        steer = desired - self.velocity
        steer = steer.limit(MAX_SPEED)
        return steer

    def flock(self, other_fighters):
        sep = self.separate(other_fighters)
        ali = self.align(other_fighters)
        coh = self.cohesion(other_fighters)
        sep *= 1.5
        ali *= 1.0
        coh *= 0.0
        return sep + ali + coh

    def separate(self, targets):
        desired_separation = 5
        steer = Vector()
        count = 0
        for target in targets:
            diff = self.position - target.position
            dist = diff.norm()
            if dist > 0 and dist < desired_separation:
                diff = diff.normalize()
                diff /= dist
                steer += diff
                count += 1
        if count > 0:
            steer /= count
            steer = steer.set_magnitude(MAX_SPEED)
            steer -= self.velocity
            steer = steer.limit(MAX_SPEED)
        logging.info(f'Separation {steer}')
        return steer

    def align(self, targets):
        neighborhood = 30
        average_velocity = Vector()
        count = 0
        for target in targets:
            dist = (self.position - target.position).norm()
            if dist > 0 and dist < neighborhood and target.velocity.norm() > 0:
                average_velocity += target.velocity
                count += 1
        if count > 0:
            average_velocity /= count
            average_velocity = average_velocity.set_magnitude(MAX_SPEED)
            steer = average_velocity - self.velocity
            steer = steer.limit(MAX_SPEED)
            logging.info(f'Alignment {steer}')
            return steer
        return Vector()

    def cohesion(self, targets):
        neighborhood = 30
        average_position = Vector()
        count = 0
        for target in targets:
            dist = (self.position - target.position).norm()
            if dist > 0 and dist < neighborhood and target.velocity.norm() > 0:
                average_position += target.position
                count += 1
        if count > 0:
            average_position /= count
            steer = self.seek(average_position)
            logging.info(f'Cohesion {steer}')
            return steer
        return Vector()

    def avoid(self, obstacles):
        max_see_ahead = 10
        ahead = self.position + self.velocity.normalize() * max_see_ahead
        ahead2 = self.position + self.velocity.normalize() * max_see_ahead * 0.5

        def line_intersects_circle(ahead, ahead2, circle_center, circle_radius):
            return (circle_center - ahead).norm() <= circle_radius or (circle_center - ahead2).norm() <= circle_radius

        most_threatening = None
        distance_to_most_threatening = 0
        for obstacle in obstacles:
            obstacle_position = Vector(obstacle.x, obstacle.y)
            distance = (self.position - obstacle_position).norm()
            collision = line_intersects_circle(
                ahead, ahead2, obstacle_position, obstacle.radius + 2)
            if collision and (most_threatening is None or distance < distance_to_most_threatening):
                most_threatening = obstacle
                distance_to_most_threatening = distance

        steer = Vector()
        if most_threatening:
            steer = ahead - Vector(most_threatening.x, most_threatening.y)
            steer.set_magnitude(MAX_SPEED)
        return steer
