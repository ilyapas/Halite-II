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

    def update(self, other_fighters):

        logging.info(f'Me {self}')
        logging.info(f'Others {other_fighters}')

        self.apply_force(self.arrive(self.target))
        self.apply_force(self.flock(other_fighters) * 0.2)

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
        coh *= 1.0
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
        neighborhood = 50
        average_velocity = Vector()
        count = 0
        for target in targets:
            dist = (self.position - target.position).norm()
            if dist > 0 and dist < neighborhood:
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
        neighborhood = 50
        average_position = Vector()
        count = 0
        for target in targets:
            dist = (self.position - target.position).norm()
            if dist > 0 and dist < neighborhood:
                average_position += target.position
                count += 1
        if count > 0:
            average_position /= count
            steer = self.seek(average_position)
            logging.info(f'Cohesion {steer}')
            return steer
        return Vector()
