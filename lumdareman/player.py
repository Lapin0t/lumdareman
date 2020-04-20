import pygame
from pygame import Vector2

from lumdareman.config import *
from lumdareman.game import CONTROL


class Player(pygame.sprite.Sprite):
    def __init__(self, image, pos_tile, ori):
        pygame.sprite.Sprite.__init__(self)

        # For rendering
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = TILE * pos_tile.x
        self.rect.y = TILE * pos_tile.y

        self.pos_tile = pos_tile
        self.pos_frac = Vector2(0., 0.)

        # Player logic
        self.ori = ori

        self.input_press = [0, 0]  # off/on  (0/1) on axis (x, y)
        self.input_last = [1, 1]   # fwd/bwd (1/-1) on axis (x, y)
        self.input_last[ori & 1] = 1 - (ori & 2)
        self.input_last_ax = ori & 1
        self.input_bomb = 0

        #self.life = PLAYER_MAX_LIFE
        #self.bombs = PLAYER_MAX_BOMBS
        #self.direction = Direction.UP # Needed to plant bomb in the right direction

    def update(self, delta_t):
        l0, l1 = self.input_last
        f0, f1 = self.pos_frac
        t0, t1 = self.pos_tile

        # rectified frac (positive == dir of movement)
        g0 = f0 * l0
        g1 = f1 * l1

        incr = delta_t * PLAYER_SPEED

        # collision check flags
        do_coll0 = False
        do_coll1 = False

        ## right/left
        if self.input_press[0]:  # move in input dir
            d0 = l0
            do_coll0 = g0 >= 0
        else:
            if g0 < 0:         # move towards middle
                d0 = l0
            elif g0 < TILE/5:  # move towards middle
                d0 = -l0
            else:              # continue last move
                d0 = l0
                do_coll0 = True

        ## down/up
        if self.input_press[1]:  # move in input dir
            d1 = l1
            do_coll1 = g1 >= 0
        else:
            if g1 < 0:         # move towards middle
                d1 = l1
            elif g1 < TILE/5:  # move towards middle
                d1 = -l1
            else:              # continue last move
                d1 = l1
                do_coll1 = True

        if do_coll0:
            if do_coll1:
                # double input collision
                c1 = (CONTROL.map[(t0 + d0, t1     )].blocking,
                      CONTROL.map[(t0     , t1 + d1)].blocking)
                c2 = CONTROL.map[(t0 + d0, t1 + d1)].blocking
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
                if CONTROL.map[(t0 + d0, t1)].blocking:
                    g0 = max(0., g0 - incr)
                else:
                    g0 = g0 + incr
                g1 = min(0., g1 + incr)
        else:
            if do_coll1:
                # down/up collision
                if CONTROL.map[(t0, t1 + d1)].blocking:
                    g1 = max(0., g1 - incr)
                else:
                    g1 = g1 + incr
                g0 = min(0., g0 + incr)
            else:
                # no collision
                g0 = min(0., g0 + incr)
                g1 = min(0., g1 + incr)

        if g0 > TILE/2:
            g0 -= TILE
            t0 += d0
        if g1 > TILE/2:
            g1 -= TILE
            t1 += d1

        f0 = g0 * d0
        f1 = g1 * d1
        self.pos_frac = (f0, f1)
        self.pos_tile = (t0, t1)

        self.rect.x = int(TILE * t0 + f0)
        self.rect.y = int(TILE * t1 + f1)

    def _update_ax(self, delta_t, ax):
        last = self.input_last[ax]
        frac = self.pos_frac[ax]
        tile = self.pos_tile[ax]
        if self.input_press[ax]:
            d = last
        else:
            if abs(frac) < 4:
                return frac/2, tile
            d = -last if 0 <= self.pos_frac[ax] * last < TILE/5 else last
        incr = delta_t * PLAYER_SPEED
        f1 = d * frac + incr
        if ax == 0:
            blk = CONTROL.map[(tile + d, self.pos_tile[1])].blocking
        else:
            blk = CONTROL.map[(self.pos_tile[0], tile + d)].blocking
        if f1 > 0 and blk:
            f1 = max(0., d * frac - incr)
        elif f1 > TILE/2:
            f1 -= TILE
            tile += d
        return d * f1, tile



    def plant_bomb(self, image):
        dx = Vector2(TILE, 0)
        dy = Vector2(0, TILE)

        if self.ori == CTRL_UP:
            bomb = Bomb(self.position - dy, image)
        elif self.ori == CTRL_DOWN:
            bomb = Bomb(self.position + dy, image)
        elif self.ori == CTRL_LEFT:
            bomb = Bomb(self.position - dx, image)
        elif self.ori == CTRL_RIGHT:
            bomb = Bomb(self.position + dx, image)

        if not pygame.sprite.spritecollide(bomb, CONTROL.solid_blocks, False):
            CONTROL.bombs.add(bomb)


