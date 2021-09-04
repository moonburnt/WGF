from WGF import GameWindow, base, RGB, AssetsLoader
from os.path import join
import logging

log = logging.getLogger(__name__)


def make_game() -> GameWindow:
    """Factory to create custom GameWindow"""
    mygame = GameWindow("Test")
    assets_directory = join(".", "Assets")
    mygame.assets = AssetsLoader(
        assets_directory=assets_directory,
        fonts_directory=join(assets_directory, "Fonts"),
        images_directory=join(assets_directory, "Sprites"),
        sounds_directory=join(assets_directory, "Sounds"),
        font_extensions=[".ttf"],
        image_extensions=[".png"],
        sound_extensions=[".ogg"],
    )
    mygame.init()

    mygame.assets.load_all()

    from Game import scenes

    mygame.tree.add(scenes.sc, default=True)

    return mygame
