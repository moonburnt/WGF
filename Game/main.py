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
    mygame.settings["vsync"] = True
    mygame.init()

    mygame.assets.load_all()

    # Modifying tree's updatemethod to implement pause support
    @mygame.tree.updatemethod
    def update():
        for event in mygame.event_handler.events:
            if event.type == base.pgl.KEYDOWN:
                if event.key == base.pgl.K_p:
                    if mygame.tree._current_child:
                        if mygame.tree._current_child.playing:
                            mygame.tree._current_child.pause()
                        else:
                            mygame.tree._current_child.play()

    from Game.scenes import intro

    mygame.tree.add(intro.sc, default=True)

    return mygame
