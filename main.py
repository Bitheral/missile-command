#!/usr/bin/python3

import pygame, sys, time, random, math
from pygame.locals import *

ramp_one, ramp_two, ramp_three = None, None, None

wood_light = (166, 124, 54)
wood_dark = (76, 47, 0)
blue = (0, 100, 255)
dark_red = (166, 25, 50)
dark_green = (25, 100, 50)
dark_blue = (25, 50, 150)
black = (0, 0, 0)
white = (255, 255, 255)

width, height = 1024, 768
screen = None

maxRadius = 60
explosions = []
delay = 100  # number of milliseconds delay before generating a USEREVENT

ground_height = height - 32

attack_missiles = []
player_missiles = []


class Bresenham:
    def __init__(self, p0, p1):
        self.initial = True
        self.end = False
        self.start = p0
        self.target = p1

        self.start_x = self.start[0]
        self.start_y = self.start[1]

        self.target_x = self.target[0]
        self.target_y = self.target[1]

        self.dx = abs(self.target_x - self.start_x)
        self.dy = abs(self.target_y - self.start_y)

        if self.start_x < self.target_x:
            self.sx = 1
        else:
            self.sx = -1

        if self.start_y < self.target_y:
            self.sy = 1
        else:
            self.sy = -1

        self.err = self.dx - self.dy

    def get_current_position(self):
        return [self.start_x, self.start_y]

    def get_next(self):
        if self.initial:
            self.initial = False
            return [self.start_x, self.start_y]

        if self.start_x == self.target_x and self.start_y == self.target_y:
            self.end = True
            return [self.target_x, self.target_y]

        if self.err * 2 > -self.dy:
            self.err -= self.dy
            self.start_x -= self.sx
        if self.err * 2 < self.dx:
            self.err += self.dx
            self.start_y += self.sy

        self.get_current_position()

    def finished(self):
        return self.end


class Explosion:
    def __init__(self, pos, maxRadius):
        self.pos = pos
        self.radius = random.randrange(1, 10)
        self.increasing = True
        self.maxRadius = maxRadius

    def draw(self):
        if self.radius > 0:
            pygame.draw.circle(screen, (255, 255, 255), self.pos, self.radius, 0)

    def update(self):
        if self.increasing:
            self.radius += 1
        else:
            self.radius -= 1

        if self.radius >= self.maxRadius:
            self.increasing = False
        elif self.radius < 0:
            global explosions
            explosions.remove(self)


class Missile:
    def __init__(self, start, destination):
        self.pos = start
        self.target = destination
        self.x = self.pos[0]
        self.y = self.pos[1]
        self.width = 8
        self.height = 16
        self.path = Bresenham(self.pos, self.target)

        self.missile_verticies = [(self.x, self.y), (self.x + (self.width / 2), self.y + (self.height / 2)),
                                  (self.x + self.width, self.y),
                                  (self.x + (self.width / 2), self.y + (self.height / 4))]

    def draw(self):
        pygame.draw.polygon(screen, (255, 255, 255), self.missile_verticies)

    def update(self):
        if self.pos == self.target:
            global missiles
            missiles.remove(this)

        if not self.path.finished():
            self.pos = self.path.get_next()

    ## TODO: Implement movement code


class Silo:
    def __init__(self, pos, w):
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
        self.launchPosition = [self.x + (self.height / 2), self.y - self.height]

    def getLaunchPosition(self):
        return self.launchPosition

    def draw(self):
        # pygame.draw.rect(screen, (255, 255, 255), self.rect)
        pygame.draw.polygon(screen, (0, 255, 0), self.mound_vertices)
        pygame.draw.rect(screen, (64, 64, 64), self.silo_rect)


class City:
    def __init__(self, pos, city_width):
        self.pos = pos
        self.center = [(pos[0] / 2), (pos[1] / 2)]
        self.width = city_width
        self.destroyed = False

        building_count = 6
        building_buffer = 6

        self.area = [self.width + (building_buffer * building_count), (self.width / 3)]
        self.rect = pygame.Rect((self.pos[0], self.pos[1] - self.area[1]), self.area)
        self.buildings = []

        for building in range(building_count):
            building_width = (self.width / building_count)
            building_height = random.randrange(int(self.width / 6), int(self.width / 2))  # * (self.width / 3)
            building_pos = [self.pos[0] + (building_buffer * building) + (building_width * building),
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

    def damage(self, pos):
        if sum(b["destroyed"] for b in self.buildings) == len(self.buildings):
            self.destroyed = True
        else:
            if self.rect.collidepoint(pos):
                rand_index = random.randrange(len(self.buildings))
                building = self.buildings[rand_index]
                while building["destroyed"]:
                    rand_index = random.randrange(len(self.buildings))
                    building = self.buildings[rand_index]

                if not building["destroyed"]:
                    building["destroyed"] = True
                    destroyed_height = int(building["rect"].height / 4)
                    old_building_rect = building["rect"]

                    building["rect"] = pygame.Rect(old_building_rect.left,
                                                   old_building_rect.top + old_building_rect.height - destroyed_height,
                                                   old_building_rect.w, destroyed_height)

    def draw(self):
        for building in self.buildings:
            if not building["destroyed"]:
                pygame.draw.rect(screen, building["colour"], building["rect"])
            else:
                pygame.draw.rect(screen, (79, 79, 79), building["rect"])


ground = pygame.Rect(0, ground_height, width, height)

cities = [City([32, ground_height], width / 8), City([width / 2 - ((width / 8) / 2) - 32, ground_height], width / 8),
          City([width - width / 8 - 64, ground_height], width / 8)]
silos = [Silo((width / 8 + 96, ground_height), 128),
         Silo((width / 2 - ((width / 8) / 2) + width / 8 + 64, ground_height), 128)]


#
# class explosion:
#     def __init__ (self, pos):
#         self._radius = 1
#         self._maxRadius = maxRadius
#         self._increasing = True
#         self._pos = pos
#
#     def update (self):
#         if self._increasing:
#             pygame.draw.circle (screen, white, self._pos, self._radius, 0)
#             self._radius += 1
#             if self._radius == self._maxRadius:
#                 self._increasing = False
#         else:
#             pygame.draw.circle (screen, black, self._pos, self._radius, 0)
#             self._radius -= 1
#             if self._radius > 0:
#                 pygame.draw.circle (screen, white, self._pos, self._radius, 0)
#             else:
#                 globalRemove (self)
#
# def createExplosion (pos):
#     global allExplosions
#     allExplosions += [explosion (pos)]
#     pygame.time.set_timer (USEREVENT+1, delay)
#
#
# def globalRemove (e):
#     global allExplosions
#     allExplosions.remove (e)
#
# def updateAll ():
#     if allExplosions != []:
#         for e in allExplosions:
#             e.update ()
#         pygame.display.flip ()
#         pygame.time.set_timer (USEREVENT+1, delay)
#
# def wait_for_event ():
#     global screen
#     while True:
#         event = pygame.event.wait ()
#         if event.type == pygame.QUIT:
#             sys.exit(0)
#         if event.type == KEYDOWN and event.key == K_ESCAPE:
#             sys.exit (0)
#         if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
#             createExplosion (pygame.mouse.get_pos ())
#         if event.type == USEREVENT+1:
#             updateAll ()
#

def createExplosion(pos, radius):
    global explosions
    explosions += [Explosion(pos, radius)]


def createPlayerMissile():
    global player_missiles
    smallest_distance = math.inf
    closest_silo = None
    for silo in silos:
        distance = math.hypot(silo.launchPosition[0] - pygame.mouse.get_pos()[0],
                              silo.launchPosition[1] - pygame.mouse.get_pos()[1])
        if distance < smallest_distance:
            smallest_distance = distance
            closest_silo = silo

    player_missiles += [Missile(closest_silo.launchPosition, pygame.mouse.get_pos())]


def main():
    global screen
    pygame.init()
    screen = pygame.display.set_mode([width, height])

    while True:
        screen.fill((128, 127, 255))
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            sys.exit(0)

        if event.type == pygame.MOUSEBUTTONDOWN:
            createExplosion(pygame.mouse.get_pos(), 5)
            createPlayerMissile()
            for city in cities:
                if not city.destroyed:
                    city.damage(pygame.mouse.get_pos())

        for city in cities:
            city.draw()

        for missile in player_missiles:
            missile.draw()
            missile.update()

        for explosion in explosions:
            explosion.draw()
            explosion.update()

        pygame.draw.rect(screen, (0, 255, 0), ground)

        for silo in silos:
            silo.draw()

        pygame.display.flip()
        pygame.time.set_timer(USEREVENT + 1, 100)
    # wait_for_event ()


main()
