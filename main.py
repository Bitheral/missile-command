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
clock = None

maxRadius = 60
explosions = []

ground_height = height - 32

attack_missiles = []
player_missiles = []


class Bresenham:
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

        if self.x0 < self.x1:
            self.sx = 1
        else:
            self.sx = -1

        if self.y0 < self.y1:
            self.sy = 1
        else:
            self.sy = -1
        self.err = self.dx - self.dy

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

    def get_current_pos(self):
        return [self.x0, self.y0]

    def finished(self):
        return self.end


class Explosion:
    def __init__(self, pos, max_radius):
        self.pos = pos
        self.radius = random.randrange(1, 10)
        self.increasing = True
        self.maxRadius = max_radius

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
        self.start_position = start

    def draw(self):
        pygame.draw.circle(screen, (255, 255, 255), self.pos, 2)
        pygame.draw.line(screen, (255, 255, 255), self.pos, self.start_position)

    def update(self):
        if not self.path.finished():
            self.pos = self.path.get_next()
        else:
            createExplosion(self.pos, 80)

            if self in player_missiles:
                player_missiles.remove(self)
            else:
                attack_missiles.remove(self)


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
        self.launchPosition = [self.x + (self.width / 2), self.y - self.height]

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
    global screen, clock
    pygame.init()
    screen = pygame.display.set_mode([width, height])
    clock = pygame.time.Clock()

    while True:
        screen.fill((128, 127, 255))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

            if event.type == pygame.MOUSEBUTTONDOWN:
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
        clock.tick(120)


main()
