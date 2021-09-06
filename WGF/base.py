import pygame
from operator import ior
from functools import reduce
from enum import Enum
import WGF

# Importing local pygame vars (usually in caps), without which "while True" fails
import pygame.locals as pgl
import logging

log = logging.getLogger(__name__)


# Pygame's Window Modes organized into enum. Few can be applied at once
class WindowMode(Enum):
    fullscreen = pygame.FULLSCREEN
    borderless = pygame.NOFRAME
    # works only in fullscreen
    hardware_acceleration = pygame.HWSURFACE
    opengl = pygame.OPENGL
    resizable = pygame.RESIZABLE
    hidden = pygame.HIDDEN
    double_buffer = pygame.DOUBLEBUF
    scaled = pygame.SCALED


# Basic event handler, in order to fix issue with pygame.event being unavailable
# from multiple places at once
# Basically its garbage to which we dump all events that occured
class EventHandler:
    events = []

    def update(self):
        self.events = pygame.event.get()


class GameContext:
    def __init__(self, cls):
        self.game = cls
        pass

    def __enter__(self):
        WGF.current_game = self.game
        return self.game

    def __exit__(self, exc_type, exc_value, exc_traceback):
        WGF.current_game = None


class GameWindow:
    """Base game window instance"""

    # Window rendering settings. To be overwritten from self.configure()
    settings: dict = {
        # #TODO: maybe also add display?
        "size": WGF.Size(1280, 720),
        "vsync": False,
        # These must be set to "False" out of box.
        "window_modes": {
            "fullscreen": False,
            "borderless": False,
            "hardware_acceleration": False,
            "opengl": False,
            "resizable": False,
            "hidden": False,
            "double_buffer": False,
            "scaled": False,
        },
    }

    # This will ensure game doesnt run faster than 60fps
    clock_speed: int = 60

    # Pygame proxies
    mouse = pygame.mouse
    window = pygame.display

    assets = None
    tree = None
    event_handler = None

    def __init__(self, title: str = "My Game"):
        log.debug("Initializing pygame")
        pygame.init()

        self.title = title
        # This is set from custom init
        self.initialized = False

    def init(self):
        """Setup game window. Basically custom init"""

        if self.initialized:
            return

        # We configuring stuff like that because user could override things manually
        # fps shenanigans
        self.clock = pygame.time.Clock()

        # Assets loader. I may want to change names l8r #TODO
        if not self.assets:
            # I dont this this path is relative to game's position on disk #TODO
            self.assets = WGF.AssetsLoader(assets_directory="Assets")
        # event handler. Only one should be active per application
        if not self.event_handler:
            self.event_handler = EventHandler()
        # Setting up window's title
        self.window.set_caption(self.title)
        # Configure is separate function, coz it may be run while game is already
        # active, to change stuff
        self.configure()
        # Scene tree
        if not self.tree:
            self.tree = WGF.scene.SceneTree()

        self.initialized = True

        WGF.game = self
        WGF.tree = self.tree

    @classmethod
    def context(cls):
        return GameContext(cls)

    # #TODO: rewrite size's hint to accept both tuples and sizes
    def configure(self, size: WGF.Size = None, vsync: bool = None, **window_modes):
        """Update window's configuration"""

        log.debug("Updating window's settings")

        self.settings["size"] = size or self.settings["size"]
        self.settings["vsync"] = vsync if vsync is not None else self.settings["vsync"]

        for mode in list(window_modes):
            m = getattr(WindowMode, mode, None)
            # No safety checks against invalid types
            if m is not None:
                self.settings["window_modes"][mode] = window_modes[mode]

        # Its necessary to add at least something to flags, or reduce will crash
        flags = [0]
        # Doing it in separate loop to preserve existing settings
        for f in list(self.settings["window_modes"]):
            if self.settings["window_modes"][f]:
                flags.append(getattr(WindowMode, f))
        flags = reduce(ior, flags)

        # Game's screen canvas. Its size is the actual size of window.
        # Mostly internal thing to measure background size
        self.screen = self.window.set_mode(
            size=self.settings["size"],
            vsync=self.settings["vsync"],
            flags=flags,
        )

        log.debug(f"Window's settings has been set to {self.settings}")

    def run(self):
        """Run the updater routine. Can only be used once"""
        if not self.initialized:
            log.warning("Unable to run game - GameWindow is not initialized")
            return

        self.tree.play()

        while True:
            self.clock.tick(self.clock_speed)
            self.event_handler.update()
            for event in self.event_handler.events:
                if event.type == pgl.QUIT:
                    log.info("Closing the game. Bye :(")
                    return
            self.tree.update()
            # This will update whats visible on screen to player
            self.window.flip()
