import pygame, pytmx
from pygame.locals import *
from pygame import Vector2

from lumdareman.config import *
from lumdareman.blocks import Block

def image_at(img, rect):
    r = pygame.Rect(rect)
    s = pygame.Surface(r.size).convert()
    s.blit(img, (0, 0), r)
    return s


def make_sheet(img, ts, ss, off=(0,0)):
    return [image_at(img, (off[0] + x*ts[0], off[1] + y*ts[1], *ts)) for y in range(ss[0]) for x in range(ss[1])]

class Control:
    def __init__(self):
        self.running = 1
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('LumDareMan')
        self.clock = pygame.time.Clock()

        self.sheet_img = pygame.image.load('assets/tileset_classic.png')
        self.sheet = make_sheet(self.sheet_img, (TILE, TILE), (8, 8))

        self.blocks = pygame.sprite.RenderUpdates()  # opt for dirty tracking
        self.solid_blocks = pygame.sprite.Group()    # just for collision
        self.destr_blocks = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()
        self.blasts = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self.map = {}

    def load_level(self, tmx_file):
        # remove old sprites
        self.blocks.empty()
        self.solid_blocks.empty()
        self.map = {}

        tmx_data = pytmx.util_pygame.load_pygame(tmx_file)
        map_data = tmx_data.layernames['blocks'].data

        global tmx
        tmx = tmx_data

        # store some stuff
        #self.tileimgs = tmx_data.images
        #self.tileprops = tmx_data.tile_properties
        self.map_w, self.map_h = tmx_data.width, tmx_data.height
        #self.tile_w, self.tile_h = tmx_data.tilewidth, tmx_data.tileheight

        self.screen = pygame.display.set_mode((self.map_w * TILE, self.map_h * TILE))

        for x in range(self.map_w):
            for y in range(self.map_h):
                gid = map_data[x][y]
                real_gid = tmx_data.tiledgidmap[gid] - 1

                Block(x, y, real_gid, self.sheet[real_gid], tmx_data.tile_properties[gid], self)

    def loop(self):

        bomberman = self.sheet[9] # Whatever, load the good tile someday
        self.player = Player(bomberman, Vector2(2, 3), 0)

        self.players.add(self.player)
        speed = .1

        while self.running:
            delta_t = self.clock.tick(FRAME_RATE)
            #player.current_input = None

            # event handling
            pygame.event.pump()
            keys = pygame.key.get_pressed()

            for ev in pygame.event.get():
                if ev.type == QUIT:
                    self.running = 0
                elif ev.type == KEYDOWN:
                    if ev.key == K_ESCAPE:
                        self.running = 0
                    elif ev.key == CONTROLS[CTRL_BOMB]:
                        self.player.input_bomb = 1
                        self.player.plant_bomb(CONTROL.sheet[8])
                    else:
                        for i in range(4):
                            if ev.key == CONTROLS[i]:
                                self.player.ori = i
                                self.player.input_last[i & 1] = 1 - (i & 2)
                                self.player.input_press[i & 1] = 1
                elif ev.type == KEYUP:
                    for i in (CTRL_LEFT, CTRL_RIGHT, CTRL_UP, CTRL_DOWN):
                        if ev.key == CONTROLS[i] and self.player.input_last[i & 1] == (1 - (i & 2)):
                            self.player.input_press[i & 1] = 0

            # state update
            self.players.update(delta_t)
            self.bombs.update(delta_t)
            self.blasts.update(delta_t)

            # rendering
            dirty = self.blocks.draw(self.screen)
            self.bombs.draw(self.screen)
            self.players.draw(self.screen)
            pygame.display.update(dirty)


CONTROL = Control()
from lumdareman.player import Player
