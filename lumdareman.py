#!/usr/bin/env python

import pygame
from pygame import Vector2
from pygame.locals import *
import pytmx

if not pygame.font: print('Warning, fonts disabled')
if not pygame.mixer: print('Warning, sound disabled')

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FRAME_RATE = 60
PLAYER_MAX_LIFE = 100
PLAYER_MAX_BOMBS = 5
BOMB_TIMER = 5 # in seconds


PLAYER_CONTROLLER = {
    'UP'   : [K_UP],
    'DOWN' : [K_DOWN],
    'LEFT' : [K_LEFT],
    'RIGHT': [K_RIGHT],
    'PLANT_BOMB' : [K_SPACE]
}

class Direction:
    UP = 'UP'
    DOWN = 'DOWN'
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'
    directions = [UP, DOWN, LEFT, RIGHT]

class Player(pygame.sprite.Sprite):
    def __init__(self, position, velocity, image):
        pygame.sprite.Sprite.__init__(self)

        # For rendering
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = position.x 
        self.rect.y = position.y

        # Player logic
        self.position = position  # Vector2
        self.velocity = velocity  # Vector2
        self.life = PLAYER_MAX_LIFE
        self.bombs = PLAYER_MAX_BOMBS
        self.direction = Direction.UP # Needed to plant bomb in the right direction

    def update(self, delta_t):
        # Check if player sprites collides with solid objects
        # if so reset velocity, else make the player move accordingly
        key_states = pygame.key.get_pressed()

        # reinventing sum(...) for lists because python version control on windows sucks
        tmp = [PLAYER_CONTROLLER[direction] for direction in Direction.directions]
        directional_keys = []
        for keys in tmp:
            directional_keys += keys

        if not any(key_states[key] for key in directional_keys):
            self.velocity /= 1.5
        
        moved_player = Player(self.position + self.velocity * delta_t, self.velocity, self.image)
        if not pygame.sprite.spritecollide(moved_player, CONTROL.solid_blocks, False):
            self.position += self.velocity * delta_t
            self.rect = self.image.get_rect()
            self.rect.x = self.position.x 
            self.rect.y = self.position.y
        else:
            self.velocity.xy = 0, 0

        # TODO: handle the case where player collides with non solid
        # objects ?

    def plant_bomb(self, image):
        dx = CONTROL.tile_w
        dy = CONTROL.tile_h

        if self.direction == Direction.UP:
            bomb = Bomb(self.position + pygame.Vector2(0, dx), image)
        elif self.direction == Direction.DOWN:
            bomb = Bomb(self.position + pygame.Vector2(0, -dx), image)
        elif self.direction == Direction.LEFT:
            bomb = Bomb(self.position + pygame.Vector2(-dy, 0), image)
        elif self.direction == Direction.RIGHT:
            bomb = Bomb(self.position + pygame.Vector2(dy, 0), image)

        if not pygame.sprite.spritecollide(bomb, CONTROL.solid_blocks, False):
            CONTROL.bombs.add(bomb)


class Bomb(pygame.sprite.Sprite):
    def __init__(self, position, image):
        pygame.sprite.Sprite.__init__(self)

        # For rendering
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = position.x
        self.rect.y = position.y

        # Bomb logic
        self.position = position  # Vector2
        self.timer = BOMB_TIMER * 1000  # miliseconds until explosion

    def update(self, delta_t):
        if self.timer < 0:
            self.kill()
            # TODO: handle explosion
        else:
            self.timer -= delta_t

class Block(pygame.sprite.DirtySprite):
    def __init__(self, x, y, gid, img, props, ctrl):
        super().__init__()

        self.ctrl = ctrl
        self.gid = gid
        self.props = props

        self.image = img
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x * TILE_X, y * TILE_Y

        ctrl.blocks.add(self)
        if props.get('blocking', 0):
            ctrl.solid_blocks.add(self)
        if props.get('destroyable', 0):
            ctrl.destr_blocks.add(self)

    def update(self, delta_t):
        pass


def image_at(img, rect):
    r = pygame.Rect(rect)
    s = pygame.Surface(r.size).convert()
    s.blit(img, (0, 0), r)
    return s


def make_sheet(img, ts, ss):
    print([(x*ts[0], y*ts[1], *ts) for x in range(ss[0]) for y in range(ss[1])])
    return [image_at(img, (x*ts[0], y*ts[1], *ts)) for y in range(ss[0]) for x in range(ss[1])]

class Control:
    def __init__(self):
        self.running = 1
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('LumDareMan')
        self.clock = pygame.time.Clock()

        self.sheet_img = pygame.image.load('assets/tileset_classic.png')
        self.sheet = make_sheet(self.sheet_img, (32, 32), (8, 8))

        self.blocks = pygame.sprite.RenderUpdates()  # opt for dirty tracking
        self.solid_blocks = pygame.sprite.Group()    # just for collision
        self.destr_blocks = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()
        self.players = pygame.sprite.Group()

    def load_level(self, tmx_file):
        # remove old sprites
        self.blocks.empty()
        self.solid_blocks.empty()

        tmx_data = pytmx.util_pygame.load_pygame(tmx_file)
        map_data = tmx_data.layernames['blocks'].data

        global tmx
        tmx = tmx_data

        # store some stuff
        #self.tileimgs = tmx_data.images
        #self.tileprops = tmx_data.tile_properties
        self.map_w, self.map_h = tmx_data.width, tmx_data.height
        #self.tile_w, self.tile_h = tmx_data.tilewidth, tmx_data.tileheight

        self.screen = pygame.display.set_mode((self.map_w * TILE_X, self.map_h * TILE_Y))

        for x in range(self.map_w):
            for y in range(self.map_h):
                gid = map_data[x][y]
                real_gid = tmx_data.tiledgidmap[gid] - 1

                Block(x, y, real_gid, self.sheet[real_gid], tmx_data.tile_properties[gid], self)

    def loop(self):

        bomberman = self.sheet[9] # Whatever, load the good tile someday
        player = Player(Vector2(2 * 32, 3 * 32), Vector2(0, 0), bomberman)

        self.players.add(player)
        speed = .1

        while self.running:
            delta_t = self.clock.tick(FRAME_RATE)
            player.current_input = None

            # event handling
            for ev in pygame.event.get():
                if ev.type == QUIT:
                    self.running = 0
                elif ev.type == KEYDOWN and ev.key == K_ESCAPE:
                    self.running = 0
                elif ev.type == KEYDOWN and ev.key in PLAYER_CONTROLLER['UP']:
                    player.velocity = Vector2(0, -speed)
                    player.direction = Direction.UP
                elif ev.type == KEYDOWN and ev.key in PLAYER_CONTROLLER['DOWN']:
                    player.velocity = Vector2(0, speed)
                    player.direction = Direction.DOWN
                elif ev.type == KEYDOWN and ev.key in PLAYER_CONTROLLER['RIGHT']:
                    player.velocity = Vector2(speed, 0)
                    player.direction = Direction.RIGHT
                elif ev.type == KEYDOWN and ev.key in PLAYER_CONTROLLER['LEFT']:
                    player.velocity = Vector2(-speed, 0)
                    player.direction = Direction.LEFT
                elif ev.type == KEYDOWN and ev.key in PLAYER_CONTROLLER['PLANT_BOMB']:
                    player.plant_bomb(self.sheet[8])


            # state update
            self.players.update(delta_t)
            self.bombs.update(delta_t)

            # rendering
            dirty = self.blocks.draw(self.screen)
            self.bombs.draw(self.screen)
            self.players.draw(self.screen)
            pygame.display.update(dirty)


if __name__ == '__main__':
    pygame.init()
    CONTROL = Control()
    CONTROL.load_level('assets/classic.tmx')
    CONTROL.loop()
    pygame.quit()
