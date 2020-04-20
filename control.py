import pygame, pytmx
from pygame.locals import *
from pygame import Vector2
from utils import *
from math import copysign




SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FRAME_RATE = 60
TILE = 32

CTRL_RIGHT = 0
CTRL_DOWN = 1
CTRL_LEFT = 2
CTRL_UP = 3
CTRL_BOMB = 4

CONTROLS = [K_RIGHT, K_DOWN, K_LEFT, K_UP, K_SPACE]
#CONTROLS = [K_e, K_o, K_a, K_COMMA, K_SPACE]



def image_at(img, rect):
    r = pygame.Rect(rect)
    s = pygame.Surface(r.size).convert()
    s.blit(img, (0, 0), r)
    return s


def make_sheet(img, ts, ss, off=(0,0)):
    print([(x*ts[0], y*ts[1], *ts) for x in range(ss[0]) for y in range(ss[1])])
    return [image_at(img, (off[0] + x*ts[0], off[1] + y*ts[1], *ts)) for y in range(ss[0]) for x in range(ss[1])]


def colliding_tiles(pos, ori, off):
    x, y = pos
   # if ori == CTRL_RIGHT:
    return {
            (int((x + TILE - .1) / TILE), int((y + off) / TILE)),
            (int((x + TILE - .1) / TILE), int((y + TILE - off) / TILE)),
   #     }
   # elif ori == CTRL_DOWN:
   #     return {
            (int((x + off) / TILE),        int((y + TILE - .1) / TILE)),
            (int((x + TILE - off) / TILE), int((y + TILE - .1) / TILE)),
   #     }
   # elif ori == CTRL_LEFT:
   #     return {
            (int((x + .1) / TILE), int((y + off) / TILE)),
            (int((x + .1) / TILE), int((y + TILE - off)/ TILE)),
   #     }
   # elif ori == CTRL_UP:
   #     return {
            (int((x + off) / TILE),        int((y + .1) / TILE)),
            (int((x + TILE - off) / TILE), int((y + .1) / TILE)),
        }

def colliding_tiles_all(x, y):
    return {
        (int((x + .1)        / TILE), int((y + .1)        / TILE)),
        (int((x + TILE - .1) / TILE), int((y + .1)        / TILE)),
        (int((x + .1)        / TILE), int((y + TILE - .1) / TILE)),
        (int((x + TILE - .1) / TILE), int((y + TILE - .1) / TILE)),
    }


PLAYER_MAX_LIFE = 100
PLAYER_MAX_BOMBS = 5

PLAYER_SPEED = 6 * TILE / 1000

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

#                elif ev.type == KEYDOWN and ev.key in PLAYER_CONTROLLER['UP']:
#                    player.velocity = Vector2(0, -speed)
#                    player.direction = Direction.UP
#                elif ev.type == KEYDOWN and ev.key in PLAYER_CONTROLLER['DOWN']:
#                    player.velocity = Vector2(0, speed)
#                    player.direction = Direction.DOWN
#                elif ev.type == KEYDOWN and ev.key in PLAYER_CONTROLLER['RIGHT']:
#                    player.velocity = Vector2(speed, 0)
#                    player.direction = Direction.RIGHT
#                elif ev.type == KEYDOWN and ev.key in PLAYER_CONTROLLER['LEFT']:
#                    player.velocity = Vector2(-speed, 0)
#                    player.direction = Direction.LEFT
#                elif ev.type == KEYDOWN and ev.key in PLAYER_CONTROLLER['PLANT_BOMB']:
#                    player.plant_bomb(self.sheet[8])


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