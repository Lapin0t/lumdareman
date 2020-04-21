import pygame
from pygame.locals import KEYUP, KEYDOWN
from pygame import Vector2

import lumdareman
from lumdareman.data import *


TURN_SLACK = TILE_SIDE / 5
START_LIFES = 4
START_BOMBS = 5
START_POWER = 4
START_SPEED = 4 * TILE_SIDE / 1000  # tile/ms


class make_player(pygame.sprite.DirtySprite):
    def __init__(self, pos_tile, ori):
        super().__init__()

        image = SHEET[9]
        self._images = [
            pygame.transform.flip(image, True, False),
            pygame.transform.rotate(image, 90),
            image,
            pygame.transform.rotate(image, -90)
        ]
        self.image = self._images[ori]

        self.rect = self.image.get_rect()
        self.rect.x = TILE_SIDE * pos_tile[0]
        self.rect.y = TILE_SIDE * pos_tile[1]
        self.dirty = 2  # always repaint
        self.layer = LAYER_PLAYER

        self.ori = ori
        self.pos_tile = pos_tile
        self.pos_frac = (0., 0.)

        self.input_press = [0, 0]  # off/on  (0/1) on axis (x, y)
        self.input_last = [1, 1]   # fwd/bwd (1/-1) on axis (x, y)
        self.input_last[ori & 1] = 1 - (ori & 2)
        self.input_bomb = 0

        self.speed = START_SPEED

        # for fast access
        self.map = lumdareman.game.GAME['level']['blocks']
        self.controls = CONFIG['controls']

        lumdareman.game.GAME['player'] = self
        lumdareman.game.GAME['sprites'].add(self)

        #self.life = PLAYER_MAX_LIFE
        #self.bombs = PLAYER_MAX_BOMBS
        #self.direction = Direction.UP # Needed to plant bomb in the right direction

    def input(self, ev):
        if ev.type == KEYDOWN:
            if ev.key == self.controls[BOMB]:
                self.input_bomb = 1
            else:
                for i in range(4):
                    if ev.key == self.controls[i]:
                        self.ori = i
                        self.image = self._images[i]
                        self.input_last[i & 1] = 1 - (i & 2)
                        self.input_press[i & 1] = 1
        elif ev.type == KEYUP:
            for i in range(4):
                if ev.key == self.controls[i] and self.input_last[i & 1] == (1 - (i & 2)):
                    self.input_press[i & 1] = 0

    def update(self, delta_t):
        self.move(delta_t)

    def move(self, delta_t):
        l0, l1 = self.input_last
        f0, f1 = self.pos_frac
        t0, t1 = self.pos_tile

        # rectified frac (positive == dir of movement)
        g0 = f0 * l0
        g1 = f1 * l1

        incr = delta_t * self.speed

        # collision check flags
        do_coll0 = False
        do_coll1 = False

        if self.input_press[0]:    # move in input dir
            d0 = l0
            do_coll0 = g0 >= 0
        else:
            if g0 < 0:             # move towards middle
                d0 = l0
            elif g0 < TURN_SLACK:  # move towards middle
                d0 = -l0
            else:                  # continue last move
                d0 = l0
                do_coll0 = True

        if self.input_press[1]:
            d1 = l1
            do_coll1 = g1 >= 0
        else:
            if g1 < 0:
                d1 = l1
            elif g1 < TURN_SLACK:
                d1 = -l1
            else:
                d1 = l1
                do_coll1 = True

        if do_coll0:
            if do_coll1:
                # double input collision
                c1 = (self.map[t0 + d0][t1].blocking, self.map[t0][t1 + d1].blocking)
                c2 = self.map[t0 + d0][t1 + d1].blocking
                g = [g0, g1]
                a0 = self.ori & 1  # prefered axis
                a1 = (a0 + 1) & 1

                if c1[a0]:  # cannot move pref direction
                    if c1[a1]:
                        g[0] = max(0., g0 - incr)
                        g[1] = max(0., g1 - incr)
                    else:
                        g[a1] = g[a1] + incr
                        g[a0] = max(0., g[a0] - incr)
                else:
                    if c1[a1] or c2:
                        g[a0] = g[a0] + incr
                        g[a1] = max(0., g[a1] - incr)
                    else:
                        g[0] = g0 + incr
                        g[1] = g1 + incr
                g0, g1 = g
            else:
                # right/left collision
                if self.map[t0 + d0][t1].blocking:
                    g0 = max(0., g0 - incr)
                else:
                    g0 = g0 + incr
                g1 = min(0., g1 + incr)
        else:
            if do_coll1:
                # down/up collision
                if self.map[t0][t1 + d1].blocking:
                    g1 = max(0., g1 - incr)
                else:
                    g1 = g1 + incr
                g0 = min(0., g0 + incr)
            else:
                # no collision
                g0 = min(0., g0 + incr)
                g1 = min(0., g1 + incr)

        if g0 > TILE_HALF:
            g0 -= TILE_SIDE
            t0 += d0
        if g1 > TILE_HALF:
            g1 -= TILE_SIDE
            t1 += d1

        f0 = g0 * d0
        f1 = g1 * d1
        self.pos_frac = (f0, f1)
        self.pos_tile = (t0, t1)

        self.rect.x = int(TILE_SIDE * t0 + f0)
        self.rect.y = int(TILE_SIDE * t1 + f1)

    def plant_bomb(self, image):
        dx = Vector2(TILE_SIDE, 0)
        dy = Vector2(0, TILE_SIDE)

        if self.ori == UP:
            bomb = Bomb(self.position - dy, image)
        elif self.ori == DOWN:
            bomb = Bomb(self.position + dy, image)
        elif self.ori == LEFT:
            bomb = Bomb(self.position - dx, image)
        elif self.ori == RIGHT:
            bomb = Bomb(self.position + dx, image)

        if not pygame.sprite.spritecollide(bomb, CONTROL.solid_blocks, False):
            CONTROL.bombs.add(bomb)
