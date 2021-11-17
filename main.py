import pygame, sys, time, random
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
allExplosions = []
delay = 100  # number of milliseconds delay before generating a USEREVENT

ground_height = height - 32


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

    def draw(self):
        # pygame.draw.rect(screen, (255, 255, 255), self.rect)
        pygame.draw.polygon(screen, (0, 255, 0), self.mound_vertices)


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
            colour = (random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255))

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

                    building["rect"] = pygame.Rect(old_building_rect.left, old_building_rect.top + old_building_rect.height - destroyed_height, old_building_rect.w, destroyed_height)

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


def main():
    global screen
    pygame.init()
    screen = pygame.display.set_mode([width, height])

    while True:
        screen.fill((0, 0, 0))
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            sys.exit(0)

        if event.type == pygame.MOUSEBUTTONDOWN:
            for city in cities:
                if not city.destroyed:
                    city.damage(pygame.mouse.get_pos())

        for city in cities:
            city.draw()

        pygame.draw.rect(screen, (0, 255, 0), ground)

        for silo in silos:
            silo.draw()

        pygame.display.flip()
    # wait_for_event ()


main()
