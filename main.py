#!/usr/bin/python3

# Imports
import math
import pygame
import random
import sys
from pygame.locals import *

ramp_one, ramp_two, ramp_three = None, None, None

# Width of the window defined to be 1280
# Height of the window defined to be 720
width, height = 1280, 720

# Window creation
screen = pygame.Surface((width, height))

# Pygame clock - This helps keep track of time in the program
clock = None

# Explosion variables
maxRadius = 60
explosions = []

# Amount of pixels above the height of the window
ground_height = height - 32

# Pygame event integers
LEFT_MOUSE_BUTTON = 1
RIGHT_MOUSE_BUTTON = 3

# Defines missiles array for attack missiles and player missiles
attack_missiles = []
player_missiles = []

# Keeps track of what tick was last updated at
last_update = 0
last_spawn = 0

"""
    Thanks to Processing/P5.js for providing the code for these two functions
    The bind function allows a value between a set of two values, to be set to another set
    For example: 0-1920 to 0-1
    https://github.com/processing/p5.js
    
    Bind function (Known as map in p5.js, renamed due to naming conviction in Python):
    https://github.com/processing/p5.js/blob/v1.4.0/src/math/calculation.js#L409
    
    Constrain function:
    https://github.com/processing/p5.js/blob/v1.4.0/src/math/calculation.js#L72
"""


# Constrains a value between a minimum and maximum value.
# (Comment taken from GitHub)
def constrain(n, low, high):
    return max(min(n, high), low)


# Binds a number from one range to another
# (Comment taken from GitHub)
def bind(value, start1, stop1, start2, stop2, withinBounds):
    new_value = (value - start1) / (stop1 - start1) * (stop2 - start2) + start2
    if not withinBounds:
        return new_value

    if start2 < stop2:
        return constrain(new_value, start2, stop2)
    else:
        return constrain(new_value, stop2, start2)


# Calculates a set of points along a line using Bresenham's algorithm
class Bresenham:

    # Initializes Bresenham's algorithm to set variables between two points
    def __init__(self, p0, p1):
        self.initial = True
        self.end = False
        self.p0 = p0
        self.p1 = p1
        self.x0 = p0[0]
        self.y0 = p0[1]
        self.x1 = p1[0]
        self.y1 = p1[1]
        self.dx = abs(self.x1 - self.x0)
        self.dy = abs(self.y1 - self.y0)
        self.e2 = 0

        if self.x0 < self.x1:
            self.sx = 1
        else:
            self.sx = -1

        if self.y0 < self.y1:
            self.sy = 1
        else:
            self.sy = -1
        self.err = self.dx - self.dy

    # Calculate next set of points depending on speed and error
    def get_next(self):
        if self.initial:
            self.initial = False
            return [self.x0, self.y0]

        if self.x0 == self.x1 and self.y0 == self.y1:
            self.end = True
            return [self.x1, self.y1]

        self.e2 = 2 * self.err
        if self.e2 > -self.dy:
            self.err = self.err - self.dy
            self.x0 = self.x0 + self.sx
        if self.e2 < self.dx:
            self.err = self.err + self.dx
            self.y0 = self.y0 + self.sy
        return [self.x0, self.y0]

    # Get current point
    def get_current_pos(self):
        return [self.x0, self.y0]

    # Check if Bresenham's algorithm has finished
    def finished(self):
        return self.end


class Explosion:

    # Initialize an explosion
    def __init__(self, pos, max_radius, missile):
        self.pos = pos
        self.radius = random.randrange(1, 10)
        self.increasing = True
        self.maxRadius = max_radius
        self.rect = pygame.Rect(self.pos[0], self.pos[1], self.radius, self.radius)
        self.parent = missile
        self.causedByPlayer = missile.isPlayer
        self.speed = 0.5

    # Draw the explosion to the screen,
    def draw(self):
        global screen

        # Checks if the explosion's radius is bigger than 0.
        # If so, draw a circle at its position with size of radius
        # If not, delete itself
        if self.radius > 0:
            pygame.draw.circle(screen, (255, 255, 255), (int(self.pos[0]), int(self.pos[1])), int(self.radius), 0)
        else:
            del self

    # Checks any other object is in range of the explosion.
    def in_range(self, other):
        if other is not self:
            return math.sqrt((self.pos[0] - other.pos[0]) ** 2 + (self.pos[1] - other.pos[1]) ** 2) <= (
                    self.radius * 2)

    # Checks if any other object is in range of the max radius limit of the explosion
    def in_max_range(self, other):
        return math.sqrt((self.pos[0] - other.pos[0]) ** 2 + (self.pos[1] - other.pos[1]) ** 2) <= (
                self.maxRadius * 2)

    # Update the explosion
    def update(self):
        # Checks if the radius has surpassed the maximum radius for the explosion
        # If so, set increasing to false
        if self.radius >= self.maxRadius:
            self.increasing = False

        # Checks if the radius is less than 0, if so, remove explosions from explosions list
        elif self.radius < 0:
            global explosions
            explosions.remove(self)

        # Checks if it's increasing, if so, increase radius, if not, decrease radius
        if self.increasing:
            self.radius += 1 * self.speed
        else:
            self.radius -= 1 * self.speed


class Missile:

    # Initialize missile
    def __init__(self, start, destination, radius=10, is_player=False):
        self.pos = start
        self.target = destination
        self.x = self.pos[0]
        self.y = self.pos[1]
        self.radius = radius
        self.path = Bresenham(self.pos, self.target)
        self.start_position = start
        self.rect = Rect(self.pos[0], self.pos[1], self.radius, self.radius)
        self.isPlayer = is_player

    # Create explosion when explode is called
    def explode(self):
        createExplosion(self.pos, 80, self)

    # Checks if this object is colliding with another object
    def collide(self, other):
        if other is not self:
            return self.rect.contains(other.rect) or self.rect.colliderect(other.rect)

    # Checks if this object is in within a threshold range of another object
    def in_range(self, other, threshold):
        if self is not other:
            return math.sqrt((self.pos[0] - other.pos[0]) ** 2 + (self.pos[1] - other.pos[1]) ** 2) <= (
                    (self.radius + threshold) * 2)

    # Draw the missile
    def draw(self):
        global screen
        pygame.draw.circle(screen, (255, 255, 255), (int(self.pos[0]), int(self.pos[1])), self.radius)
        pygame.draw.line(screen, (255, 255, 255), (int(self.pos[0]), int(self.pos[1])), self.start_position)

    # Update the missile
    def update(self):
        # Checks if the missile has gone through all points in Bresenham's algorithm
        # If not, set current position to the next point in Bresenham's algorithm
        # If so, explode the missile, and remove the missile from its list
        if not self.path.finished():
            self.pos = self.path.get_next()
        else:
            self.explode()

            if self in player_missiles:
                player_missiles.remove(self)
            else:
                attack_missiles.remove(self)


class Silo:
    global screen

    # Initialize class into an instance
    def __init__(self, pos, w):
        global last_update
        self.pos = pos
        self.missiles = 6
        self.width = w
        self.height = w / 4
        self.x = pos[0]
        self.y = pos[1]
        self.mound_vertices = [(self.x, self.y), (self.x + self.width, self.y),
                               (self.x + self.width - (self.width / 4), self.y - self.height),
                               (self.x + (self.width / 4), self.y - self.height)]

        self.silo_rect = pygame.Rect(self.x + self.height, self.y - self.height - 4,
                                     self.width - (self.height + self.height), height - self.height)
        self.launchPosition = [self.x + (self.width / 2), self.y - self.height]
        self.reload_time = 0
        self.max_missiles = 6

    # Get position where missiles should launch from
    def getLaunchPosition(self):
        return self.launchPosition

    # Update the missile
    def update(self):
        # Checks if it has been longer than 1.5 seconds
        # and that the missiles is less than max missiles
        # before reloading
        if last_update - self.reload_time >= 1500 and self.missiles < self.max_missiles:
            self.missiles += 1

    # Draw missile
    def draw(self):
        pygame.draw.polygon(screen, (0, 255, 0), self.mound_vertices)
        pygame.draw.rect(screen, (64, 64, 64), self.silo_rect)

        ammo_radius = 4

        # Draw ammunition pellets in the middle of the silo, depending on how many missiles the silos have
        for ammo in range(self.missiles):
            ammo_pos = (int(self.x + (self.height + ((ammo_radius * 2) + ammo_radius / 2) * ammo) + ammo_radius * 1.5),
                        int(self.y + self.height / 2))
            pygame.draw.circle(screen, (255, 255, 255), ammo_pos, int(ammo_radius), 0)


class City:
    global screen

    # Initialize city
    def __init__(self, pos, city_width):
        self.pos = pos
        self.width = city_width
        self.destroyed = False
        self.center = [self.pos[0] + (self.width / 2), self.pos[1] - (int(self.width / 2) / 2)]

        # Limit the building count
        self.building_count = 6

        # Pixel difference per building
        self.building_buffer = 6

        # Calculate area which should cause the city to be affected by missiles
        self.area = [self.width + (self.building_buffer * self.building_count), (self.width / 3)]
        self.rect = pygame.Rect(self.pos[0], self.pos[1] - int(self.width / 2),
                                self.width + (self.building_buffer * self.building_count), int(self.width / 2))
        self.buildings = []

        # Create the building, and calculate where to place them
        for building in range(self.building_count):
            building_width = (self.width / self.building_count)
            building_height = random.randrange(int(self.width / 6), int(self.width / 2))
            building_pos = [self.pos[0] + (self.building_buffer * building) + (building_width * building),
                            self.pos[1] - building_height]

            rect = pygame.Rect(building_pos, (building_width, building_height))
            colour_one = random.randrange(15, 63)
            colour = (colour_one, colour_one, colour_one)

            building_dict = {
                "rect": rect,
                "colour": colour,
                "destroyed": False
            }
            self.buildings.append(building_dict)

        self.repairing = False
        self.repair_start = 0
        self.repair_progress = 0
        self.repair_progress_width = 0
        self.repair_rect = pygame.Rect(self.pos[0],
                                       self.pos[1] - int(self.width / 2) - 32,
                                       0,
                                       16)

    # Cause damage to the city
    def damage(self):
        # Checks if the city is not destroyed
        if not self.destroyed:
            # Checks if all buildings in a city is destroyed
            # If so, declare the city to be destroyed
            # If not, pick a random building, and destroy it
            if sum(b["destroyed"] for b in self.buildings) == len(self.buildings):
                self.destroyed = True
            else:
                rand_index = random.randrange(len(self.buildings))
                building = self.buildings[rand_index]

                if not building["destroyed"]:
                    building["destroyed"] = True
                    destroyed_height = int(building["rect"].height / 4)
                    old_building_rect = building["rect"]

                    building["destroyed_rect"] = pygame.Rect(old_building_rect.left,
                                                             old_building_rect.top + old_building_rect.height - destroyed_height,
                                                             old_building_rect.w, destroyed_height)

    # Repair city
    def repair(self):
        self.repair_start = pygame.time.get_ticks()
        self.repairing = True

    # Draw the city
    def draw(self):
        # Draw every building in the buildings list
        # If the building is destroyed, draw it with its colour,
        # If not, draw it with a light grey
        for building in self.buildings:
            if not building["destroyed"]:
                pygame.draw.rect(screen, building["colour"], building["rect"])
            else:
                pygame.draw.rect(screen, (79, 79, 79), building["destroyed_rect"])

        # Only show the repair progress if the city is being repaired
        if self.repairing:
            pygame.draw.rect(screen, (255, 255, 255), self.repair_rect)

    # Update the city
    def update(self):

        # Checks if the city is being repaired
        if self.repairing:

            # Calculate the width of the rect based on the progress of the repair
            self.repair_progress = last_update - self.repair_start
            self.repair_rect.width = bind(self.repair_progress, 0, 4000, 0,
                                          self.width + (self.building_buffer * self.building_count), True)

            # If the repair has taken more than 4 seconds, then reset state of the city
            if self.repair_progress >= 4000:
                self.repairing = False
                self.destroyed = False
                for building in self.buildings:
                    building["destroyed"] = False


# Ground surface
ground = pygame.Rect(0, ground_height, width, height)

# List of cities, placed depending on screen size
cities = [City([32, ground_height], width / 8), City([width / 2 - ((width / 8) / 2) - 32, ground_height], width / 8),
          City([width - width / 8 - 64, ground_height], width / 8)]

# List of silos, placed depending on screen size
silos = [Silo((width / 8 + 96, ground_height), 128),
         Silo((width / 2 - ((width / 8) / 2) + width / 8 + 64, ground_height), 128)]


# Create an explosion
def createExplosion(pos, radius, parent):
    global explosions

    # Add to explosions list with parameters
    explosions += [Explosion(pos, radius, parent)]


# Create a missile, created by the player
def createPlayerMissile():
    global player_missiles

    # Calculate closest silo, depending on mouse position
    smallest_distance = math.inf
    closest_silo = None
    for silo in silos:
        distance = math.hypot(silo.launchPosition[0] - pygame.mouse.get_pos()[0],
                              silo.launchPosition[1] - pygame.mouse.get_pos()[1])
        if distance < smallest_distance and silo.missiles > 0:
            smallest_distance = distance
            closest_silo = silo

    # Checks if there's a silo nearby
    if closest_silo is not None:
        # Added missile to player missiles list, remove a missile and set reload time
        player_missiles += [Missile(closest_silo.launchPosition, pygame.mouse.get_pos(), is_player=True)]
        closest_silo.missiles -= 1
        closest_silo.reload_time = pygame.time.get_ticks()


# Create a missile, created by the attacker / computer
def createAttackMissile():
    global cities, attack_missiles, clock, last_update, last_spawn

    max_missiles = 5
    now = pygame.time.get_ticks()

    # Picks a random value between 0 and width of the window
    start_x = random.randint(0, width)
    start_y = ground_height - height
    start = [start_x, start_y]

    # Calculates the closest city depending on starting position
    smallest_distance = math.inf
    closest_city = None
    for city in cities:
        distance = math.hypot(city.center[0] - start_x,
                              city.center[1] - start_y)
        if distance < smallest_distance and not city.destroyed:
            smallest_distance = distance
            closest_city = city

    # If there is no city nearby, set the target x to be random value between 0 and width of the window
    # If there is a city nearby, set the target x to be the center of the city
    if closest_city is None:
        end_x = random.randint(0, width)
    else:
        end_x = closest_city.center[0]

    end = [end_x, ground_height]

    # Checks if it's been longer than 1.5 seconds
    # and there is less than max_missiles (6)
    # before creating another missile
    if now - last_spawn >= 1500 and len(attack_missiles) < max_missiles:
        attack_missiles += [Missile(start, end)]
        last_spawn = now


def main():
    global screen, clock, last_update

    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode([width, height])
    pygame.display.set_caption("Missile Command")
    clock = pygame.time.Clock()

    # Game loop
    while True:
        # Render sky
        screen.fill((128, 127, 255))

        # Checks how many cities are destroyed
        destroyed_cities = [city for city in cities if city.destroyed]

        # Checks if the destroyed_cities list is not the same as cities list
        # If so, create attack missiles
        # If not (If all cities are destroyed) explode all attack missiles
        if not destroyed_cities == cities:
            createAttackMissile()
        else:
            for attack in attack_missiles:
                attack.explode()

        # Checks if user has interacted with pygame window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

            # Checks if user has clicked using the mouse
            if event.type == pygame.MOUSEBUTTONDOWN:

                # Checks if the user has clicked with the left mouse button
                # If so, create a player missile
                if event.button == LEFT_MOUSE_BUTTON:
                    createPlayerMissile()

                # Checks if the user has clicked with the right mouse button
                # If so, check if the user has clicked over any of the cities,
                # and if so, repair the city if the city is destroyed
                if event.button == RIGHT_MOUSE_BUTTON:
                    for city in cities:
                        if city.rect.collidepoint(pygame.mouse.get_pos()) and city.destroyed and not city.repairing:
                            city.repair()

        # Draw and update all cities
        for city in cities:
            city.draw()
            city.update()

        # Draw and update all player missiles
        for missile in player_missiles:
            missile.draw()
            missile.update()

            # Check if any attack and player missiles collide
            # If so, explode them and remove them of their
            # respective lists
            for attack in attack_missiles:
                if missile.in_range(attack, -5):
                    missile.explode()
                    attack.explode()
                    player_missiles.remove(missile)
                    attack_missiles.remove(attack)

        # Draw and update all attack missiles
        for missile in attack_missiles:
            missile.draw()
            missile.update()

        # Draw and update all explosions
        for explosion in explosions:
            explosion.draw()
            explosion.update()

            # Checks if the explosion is in range of a city
            # and if it was an attack missile
            # If so, damage the city
            for city in cities:
                if explosion.in_max_range(city) and not explosion.causedByPlayer:
                    city.damage()

            # Checks if the explosion is in range of an attack missile
            # If so, explode the missile and remove it from attack missiles list
            for attack in attack_missiles:
                if explosion.in_range(attack):
                    attack.explode()
                    attack_missiles.remove(attack)

        # Draw the ground
        pygame.draw.rect(screen, (0, 255, 0), ground)

        # Draw all silos and update them
        for silo in silos:
            silo.draw()
            silo.update()

        # Progress onto next frame
        pygame.display.flip()
        clock.tick(60)
        last_update = pygame.time.get_ticks()


main()
