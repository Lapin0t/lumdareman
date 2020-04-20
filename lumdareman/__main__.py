#!/usr/bin/env python

import pygame

from pygame.locals import *

from lumdareman.game import CONTROL


if not pygame.font: print('Warning, fonts disabled')
if not pygame.mixer: print('Warning, sound disabled')



if __name__ == '__main__':
    pygame.init()
    CONTROL.load_level('assets/empty.tmx')
    CONTROL.loop()
    pygame.quit()
