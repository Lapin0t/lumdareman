import pygame, pytmx
from pygame.locals import *
from pygame import Vector2

from lumdareman.data import *
import lumdareman.game


class make_block(pygame.sprite.DirtySprite):
    def __init__(self, x, y, gid):
        super().__init__()

        self.gid = gid
        #self.props = props

        self.image = SHEET[gid]
        self.layer = LAYER_MAP
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x * TILE_SIDE, y * TILE_SIDE

        self.blocking = gid in (0, 1)

        # register globally
        lumdareman.game.GAME['sprites'].add(self)
        lumdareman.game.GAME['level']['blocks'][x][y] = self

    def update(self, delta_t):
        pass
