from WGF import game
from pygame import transform, sprite
import logging

log = logging.getLogger(__name__)

# Tasks that require game's clock tickin'


class Animation:
    """Animation consisting of multiple sprites"""

    # #TODO: add storage to keep flipped sprites

    def __init__(
        self,
        sprites: list,
        loop: bool = True,
        default_frame: int = 0,
        scale: int = None,
        speed: float = 160,
    ):
        if scale:
            # This will fail if size of sprites is not the same
            x, y = sprites[0].get_size()
            x = x * scale
            y = y * scale
            sprites = [transform.scale(img, (x, y)) for img in sprites]

        self.sprites = sprites
        self.loop = loop
        self.current_frame = default_frame
        self.speed = speed

        self._time = speed

    def __iter__(self):
        for var in self.sprites:
            yield var

    def __getitem__(self, key: int):
        return self.sprites[key]

    def next(self):
        self._time -= game.clock.get_time()
        if self._time <= 0:
            self._time = self.speed
        else:
            return None
        if self.current_frame == len(self.sprites):
            if not self.loop:
                return None
            else:
                self.current_frame = 0

        img = self.sprites[self.current_frame]
        self.current_frame += 1
        return img

    def flip(self, horizontally: bool = False, vertically: bool = False):
        if horizontally or vertically:
            self.sprites = [
                transform.flip(spr, horizontally, vertically) for spr in self.sprites
            ]
