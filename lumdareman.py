#!/usr/bin/env python

import pygame

from utils import *
from pygame import Vector2
from pygame.locals import *
from math import copysign
from control import CONTROL
from control import *


if not pygame.font: print('Warning, fonts disabled')
if not pygame.mixer: print('Warning, sound disabled')



if __name__ == '__main__':
    pygame.init()
    CONTROL.load_level('assets/empty.tmx')
    CONTROL.loop()
    pygame.quit()
