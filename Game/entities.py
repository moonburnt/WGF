from pygame import mouse, sprite, Surface, display, transform
from WGF import game
import logging

log = logging.getLogger(__name__)


class Entity(sprite.Sprite):
    scale = 0

    def __init__(self):
        super().__init__()
        # print(self.scale)
        if self.scale:
            size = self.image.get_size()
            x = size[0] * self.scale
            y = size[1] * self.scale
            self.image = transform.scale(self.image, (x, y))

        self.rect = self.image.get_rect()


class Enemy(Entity):
    scale: int = 4
    horizontal_speed: int = 4
    # Rotation angle. If not 0, character will start spinning
    angle: int = 0

    def __init__(self):
        self.image = game.assets.images["enemy"]
        super().__init__()

        # Make it possible for entity to move around screen-sized area
        self.area = display.get_surface().get_rect()
        # This will set position of creature to spawn on, from top left corner of
        # creature's rectangle
        self.rect.topleft = (10, 400)
        # I have no idea how this works, probably underlying c shenanigans
        # But basically this doesnt just reffer to self.image, but clone it
        self.original = self.image

    def update(self):
        """Make entity do different things, depending on current status effects"""
        if self.angle:
            self.spin()
        else:
            self.walk()

    def walk(self):
        """Make entity walk across the screen and turn at its corners"""
        # For now it can only move horizontally
        pos = self.rect.move((self.horizontal_speed, 0))
        # Ensuring new position wouldnt be out of screen's bounds
        # For now, only checks for horizontal "out of bounds" situations
        if not self.area.contains(pos):
            self.horizontal_speed = -self.horizontal_speed
            pos = self.rect.move((self.horizontal_speed, 0))
            # This will flip image horizontally
            self.image = transform.flip(self.image, True, False)

        self.rect = pos

    def spin(self):
        """Spin enemy's img"""
        center = self.rect.center
        self.angle += 12
        if self.angle >= 360:
            self.angle = 0
            self.image = self.original
        else:
            rotate = transform.rotate
            self.image = rotate(self.original, self.angle)
        self.rect = self.image.get_rect(center=center)

    def damaged(self):
        if not self.angle:
            self.angle = 1
            self.original = self.image


# #TODO: rework this into "weapon", make it serve as base for others
class Greatsword(Entity):
    scale: int = 2
    attacking: bool = False

    def __init__(self):
        self.image = game.assets.images["greatsword"]
        super().__init__()

    def update(self):
        self.rect.midtop = mouse.get_pos()
        if self.attacking:
            self.rect.move_ip(5, 10)

    def hit(self, target: Enemy) -> bool:
        """Attack target with weapon and check if collision has happend"""
        if self.attacking:
            return False

        self.attacking = True
        hitbox = self.rect.inflate(-5, 5)
        return hitbox.colliderect(target.rect)

    def pullback(self):
        self.attacking = False
