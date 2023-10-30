#!/usr/bin/env python3
import sys
import pygame
###
###
# Define some colors
##
##
import math
from itertools import cycle

##
def Gui_pop(image):
  screen = pygame.display.set_mode((1000, 800))
  o = pygame.image.load('Mayhem.png')
  clock = pygame.time.Clock()
  background = pygame.image.load('lightning.jpeg')
  screen.blit(background, (0, 0))
  objects = []
  objects.append(o)##You can add many objects
  while True:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        sys.exit()
    for o in objects:
      screen.blit(background, (0, 0))
    for o in objects:
      screen.blit(o, (8, 2))
      pygame.display.update()
      clock.tick(60)

if __name__ == "__main__":
  Gui_pop()
