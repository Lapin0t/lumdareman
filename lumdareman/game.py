import pygame
from pygame.locals import *
from pygame import Vector2
from random import randrange

from lumdareman.data import CONFIG, get_map_data, TILE_SIDE
from lumdareman.block import make_block
from lumdareman.player import make_player


GAME = {
    'clock': pygame.time.Clock(),
    'sprites': pygame.sprite.LayeredDirty()
}


def load_level(tm_path):
    GAME['sprites'].empty()

    tm = get_map_data(tm_path)
    w, h = tm['size']

    GAME['level'] = {
        'size': tm['size'],
        'blocks': [[None] * w for _ in range(h)],
        'spawns': [],
    }

    GAME['screen'] = pygame.display.set_mode((w * TILE_SIDE, h * TILE_SIDE))
    pygame.display.set_caption(tm['title'])

    for y in range(h):
        for x in range(w):
            make_block(x, y, tm['data'][y*w + x] - 1)

    make_player((3, 3), 0) # TODO spawn


def main_loop():
    clock_tick = GAME['clock'].tick
    framerate = CONFIG['framerate']
    screen = GAME['screen']
    player_input = GAME['player'].input
    sprites_update = GAME['sprites'].update
    sprites_draw = GAME['sprites'].draw
    display_update = pygame.display.update
    event_get = pygame.event.get

    while True:
        delta_t = clock_tick(framerate)

        for ev in event_get():
            if ev.type == QUIT:
                return
            player_input(ev)

        sprites_update(delta_t)
        dirty = sprites_draw(screen)
        display_update(dirty)

def quit():
    pygame.quit()
