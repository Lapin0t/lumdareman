import array, base64, configparser, json, os
import pygame
import lumdareman


def load_config(path):
    parser = configparser.ConfigParser()
    parser.read(path)

    try:
        config = {
            'framerate': parser.getint('general', 'frame_rate'),
            'controls': [
                getattr(pygame.locals, parser.get('controls', c))
                for c in ('right', 'down', 'left', 'up')
            ],
        }
    except Exception:
        print("Warning: config error, using default")
        config = DEFAULT_CONFIG

    CONFIG.update(config)


_MAP_DATA = {}
def get_map_data(tm_file):
    if tm_file not in _MAP_DATA:
        with open(os.path.join(ROOT_DIR, 'assets', tm_file)) as s:
            tm_data = json.load(s)

        w, h = tm_data['width'], tm_data['height']
        title = tm_data.get('properties', {}).get('title', '')

        if len(tm_data.get('layers', [])) != 1:
            raise ValueError('%s is not a valid map' % tm_path)
        layer = tm_data['layers'][0]
        if 'data' not in layer:
            raise ValueError('%s is not a valid map' % tm_path)
        map_data = array.array('i', base64.decodebytes(layer['data'].encode('ascii')))

        _MAP_DATA[tm_file] = {
            'size': (w, h),
            'title': title,
            'data': map_data
        }
    return _MAP_DATA[tm_file]


def image_at(img, rect):
    r = pygame.Rect(rect)
    s = pygame.Surface(r.size).convert()
    s.blit(img, (0, 0), r)
    return s

def make_sheet(img, ts, ss, off=(0,0)):
    return [image_at(img, (off[0] + x*ts[0], off[1] + y*ts[1], *ts)) for y in range(ss[0]) for x in range(ss[1])]


DEFAULT_CONFIG = {
    'framerate': 60,
    'controls': [
        #pygame.locals.K_RIGHT,
        #pygame.locals.K_DOWN,
        #pygame.locals.K_LEFT,
        #pygame.locals.K_UP,
        #pygame.locals.K_SPACE,
        pygame.locals.K_e,
        pygame.locals.K_o,
        pygame.locals.K_a,
        pygame.locals.K_COMMA,
        pygame.locals.K_SPACE,
    ]
}

CONFIG = DEFAULT_CONFIG

# a couple useful constants
TILE_SIDE = 32
TILE_HALF = 16
RIGHT, DOWN, LEFT, UP, BOMB = range(5)
ROOT_DIR = os.path.dirname(lumdareman.__path__[0])
LAYER_MAP, LAYER_POWERUP, LAYER_PLAYER, LAYER_TOP = range(4)

BOMB_TIMER = 5 # seconds
BLAST_TIMER = 2 # seconds
BLAST_PROPAGATION_TIMER = .2 # seconds
BLAST_RADIUS = 2

SHEET = make_sheet(pygame.image.load('assets/tileset_classic.png'), (TILE_SIDE, TILE_SIDE), (8, 8))

