import pygame
from pygame import Vector2
from utils import Direction
from control import CONTROL

BOMB_TIMER = 5 # seconds
BLAST_TIMER = 2 # seconds
BLAST_PROPAGATION_TIMER = .2 # seconds
BLAST_RADIUS = 2

# Useful when we'll have directional explosion
BLAST_SHEET = {
    "CENTER"    : CONTROL.sheet[18],
    "NOT_CENTER": CONTROL.sheet[17]
}

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
        self.blast_radius = BLAST_RADIUS 

    def update(self, delta_t):
        if self.timer < 0:
            blast = Blast(self.position, self.radius, center = True) # center of the blast
            CONTROL.blasts.add(blast)
            self.kill()
        else:
            self.timer -= delta_t


class Blast(pygame.sprite.Sprite):
    def __init__(self, position, radius, direction = None, center = False):
        pygame.sprite.Sprite.__init__(self)

        # For rendering
        self.image = self.load_image()
        
        self.rect = self.image.get_rect()
        self.rect.x = position.x
        self.rect.y = position.y

        # Blast logic (timers in millisec)
        self.timer = BLAST_TIMER * 1000
        self.propagation_timer = BLAST_PROPAGATION_TIMER * 1000
        self.direction = direction
        self.radius = radius
    
    def load_image(self):
        """ Return the right sprite for the blast """
        if self.center:
            return BLAST_SHEET["CENTER"]
        else:
            return BLAST_SHEET["NOT_CENTER"]
        

    def propagate(self):
        new_radius = self.radius - 1
        if new_radius < 1:
            return
         
        dx = Vector2(TILE, 0)
        dy = Vector2(0, TILE)
        pos = self.position

        blasts = {
            Direction.LEFT  : Blast(pos - dx, new_radius, direction = Direction.LEFT),
            Direction.RIGHT : Blast(pos + dx, new_radius, direction = Direction.RIGHT),
            Direction.UP    : Blast(pos - dy, new_radius, direction = Direction.UP),
            Direction.DOWN  : Blast(pos + dy, new_radius, direction = Direction.DOWN)
        }

        if center:
            CONTROL.blast.add(blasts.values())
        else:
            # TODO: if (nothing blocks the blasts):
            CONTROL.blast.add(blasts[self.direction])
        
    def update(self, delta_t):
        
        if self.propagation_timer >= 0:
            self.propagation_timer -= delta_t

            if self.propagation_timer < 0:
                self.propagate()

        if self.timer >= 0:
            self.timer -= delta_t

            if self.timer < 0:
                self.kill()     
        
        


    



