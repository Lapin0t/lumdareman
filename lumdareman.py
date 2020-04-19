#!/usr/bin/env python

import pygame
from pygame.locals import *
import pytmx

if not pygame.font: print('Warning, fonts disabled')
if not pygame.mixer: print('Warning, sound disabled')

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FRAME_RATE = 60
PLAYER_MAX_LIFE = 100
PLAYER_MAX_BOMBS = 5
BOMB_TIMER = 5


class Level:
    def __init__(self, tmx_file, ctrl):
        self.ctrl = ctrl
        tmx_data = pytmx.util_pygame.load_pygame(tmx_file)

        self.map_w, self.map_h = tmx_data.width, tmx_data.height
        self.tile_w, self.tile_h = tmx_data.tilewidth, tmx_data.tileheight

        self.imgs = tmx_data.images
        self.props = tmx_data.tile_properties
        self.tiles = tmx_data.layernames['blocks'].data

        self.make_sprites()

    def make_sprites(self):
        for x in range(self.map_w):
            for y in range(self.map_h):
                gid = self.tiles[x][y]

                sp = pygame.sprite.DirtySprite()
                sp.image = self.imgs[gid]
                sp.rect = sp.image.get_rect()
                sp.rect.x, sp.rect.y = x * self.tile_w, y * self.tile_h
                sp.add(self.ctrl.blocs)
                if self.props[gid].get('blocking', 0):
                    sp.add(self.ctrl.solid_blocs)


class Player(pygame.sprite.Sprite):
    def __init__(self, position, velocity, image):
        pygame.sprite.Sprite.__init__(self)

        # For rendering
        self.image = image
        self.rect = self.image.get_rect()

        # Player logic
        self.position = position  # Vector2
        self.velocity = velocity  # Vector2
        self.life = PLAYER_MAX_LIFE
        self.bombs = PLAYER_MAX_BOMBS


    def update(self, delta_t):
        # Check if player sprites collides with solid objects
        # if so reset velocity, else make the player move accordingly
        if not pygame.sprite.spritecollide(self, STATE.solid_blocks, False):
            self.position += self.velocity * delta_t
        else:
            self.position.xy = 0, 0
        # TODO: handle the case where player collides with non solid
        # objects ?

class Bomb(pygame.sprite.Sprite):
    def __init__(self, position, image):
        pygame.sprite.Sprite.__init__(self)

        # For rendering
        self.image = image
        self.rect = self.image.get_rect()

        # Bomb logic
        self.position = position  # Vector2
        self.timer = BOMB_TIMER   # seconds until explosion

    def update(self, delta_t):
        if timer < 0:
            self.kill()
            # TODO: handle explosion
        else:
            self.timer -= delta_t
        


class Control:
    def __init__(self):
        self.running = 1
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('LumDareMan')
        self.clock = pygame.time.Clock()

        self.blocs = pygame.sprite.RenderUpdates()  # opt for dirty tracking
        self.solid_blocs = pygame.sprite.Group()   # just for collision
        self.bombs = pygame.sprite.Group()
        self.players = pygame.sprite.Group()

        self.level = Level('assets/classic.tmx', self)
    
    def loop(self):
        while self.running:
            delta_t = self.clock.tick(FRAME_RATE)

            # event handling
            for ev in pygame.event.get():
                if ev.type == QUIT:
                    self.running = 0
                elif ev.type == KEYDOWN and ev.key == K_ESCAPE:
                    self.running = 0

             # state update

            # rendering
            dirty = self.blocs.draw(self.screen)
            self.bombs.draw(self.screen)
            self.players.draw(self.screen)
            pygame.display.update(dirty)


if __name__ == '__main__':
    pygame.init()
    CONTROL = Control()
    CONTROL.loop()
    pygame.quit()
