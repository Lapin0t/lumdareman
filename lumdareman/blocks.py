import pygame, pytmx
from pygame.locals import *
from pygame import Vector2

from lumdareman.config import *


class Block(pygame.sprite.DirtySprite):
    def __init__(self, x, y, gid, img, props, ctrl):
        super().__init__()

        self.ctrl = ctrl
        self.gid = gid
        self.props = props

        self.image = img
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x * TILE, y * TILE

        ctrl.blocks.add(self)
        ctrl.map[x,y] = self
        self.blocking = props.get('blocking', 0)
        self.destroyable = props.get('destroyable', 0)

    def update(self, delta_t):
        pass
