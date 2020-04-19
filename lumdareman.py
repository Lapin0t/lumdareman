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

class LevelMap:
    def __init__(self, tmx_file):
        self.tmx_data = pytmx.util_pygame.load_pygame(tmx_file)
        self.tw = self.tmx_data.tilewidth
        self.th = self.tmx_data.tileheight
        self.get_tile = self.tmx_data.get_tile_image_by_gid

    def render(self, surface):
        if self.tmx_data.background_color:
            surface.fill(self.tmx_data.background_color)

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for (x, y, gid) in layer:
                    tile = self.get_tile(gid)
                    surface.blit(tile, (x * self.tw, y * self.th))

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
    
class GameState:
    def __init__(self, screen):
        self.screen = screen
        self.running = 1
        self.clock = pygame.time.Clock()

        self.solid_blocks = pygame.sprite.LayeredUpdates()
        self.sprites = pygame.sprite.LayeredUpdates()
        self.level = LevelMap('assets/classic.tmx')

    def loop(self):
        while self.running:
            delta_t = self.clock.tick(FRAME_RATE)

            for ev in pygame.event.get():
                if ev.type == QUIT:
                    self.running = 0
                elif ev.type == KEYDOWN and ev.key == K_ESCAPE:
                    self.running = 0

            self.sprites.update()
            self.sprites.draw(self.screen)
            self.level.render(self.screen)
            pygame.display.flip()


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('LumDareMan')

    STATE = GameState(screen)
    state.loop()

    pygame.quit()
