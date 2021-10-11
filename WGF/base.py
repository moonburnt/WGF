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


class Camera:
    """Simple camera node"""

    def __init__(self, pos: WGF.Point = WGF.Point(0, 0)):
        self.pos = pos


class NodeBase:
    def __init__(self, name):
        self.name = name
        self._children = {}

    def __repr__(self):
        return f"{type(self).__name__}"

    def add_child(self, node, name: str = None, show: bool = True):
        # if isinstance(node, Node):
        node.init()
        if show:
            node.show()
        name = name or node.name
        self._children[name] = node

    @property
    def children(self):
        # This isnt the best way to handle it, but I want to return children as
        # read-only property, so it will do... I guess
        return tuple(self._children.values())

    def __setitem__(self, key: str, value):
        value.init()
        self._children[key] = value

    def __getitem__(self, key: str):
        return self._children[key]

    def draw(self):
        pass

    def __iter__(self):
        for var in self._children:
            yield var, self._children[var]

    def __delitem__(self, key):
        del self._children[key]


class SceneTree(NodeBase):
    def __init__(self):
        super().__init__(name="root")
        self.draw_list = []

    def update(self):
        self.draw_list = []
        for item in self._children.values():
            item.update()

        for i in self.draw_list:
            i.draw()


class GameContext:
    def __init__(self, cls):
        self.game = cls
        pass

    def __enter__(self):
        WGF.current_game = self.game
        return self.game

    def __exit__(self, exc_type, exc_value, exc_traceback):
        WGF.current_game = None


def rmerge(x: dict, y: dict) -> dict:
    """Merge two dicts recursively"""

    new = x.copy()
    for i in y:
        val = y[i]
        if i in new and isinstance(new[i], dict) and isinstance(val, dict):
            val = rmerge(new[i], val)
        new[i] = val

    return new


class SettingsManager:
    """Settings manager"""

    def __init__(self):
        # Default window rendering settings, which should be used as fallback
        self._default = {
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
        self.reset()

    def __getitem__(self, key: str):
        return self._storage[key]

    def __setitem__(self, key: str, value):
        self._storage[key] = value

    def reset(self):
        """Reset settings to defaults"""
        self._storage = self._default.copy()

    def set_default(self, key: str, value):
        """Set default value of provided argument"""
        self._default[key] = value

        # Also updating storage, in case it didnt have this
        if not key in self._storage:
            self._storage[key] = value

    def from_dict(self, data: dict):
        """Update settings from provided dict"""

        # Using recursive merge coz otherwise window_modes may be butchered
        self._storage = rmerge(self._storage, data)

    def to_dict(self) -> dict:
        """Dump current settings into dictionary"""
        return self._storage.copy()

    def from_toml(self, filepath):
        """Update settings from provided .toml file"""

        try:
            import toml

            data = toml.load(filepath)
        except Exception as e:
            log.warning(f"Unable to update settings from {filepath} toml: {e}")
        else:
            self.from_dict(data)
            log.debug(f"Successfully updated settings to {self._storage}")

    def to_toml(self, filepath):
        """Dump current settings to provided .toml file"""

        try:
            import toml

            with open(filepath, "w") as f:
                toml.dump(self._storage, f)
        except Exception as e:
            log.warning(f"Unable to save settings to {filepath} toml: {e}")
        else:
            log.debug(f"Successfully saved settings to {filepath}")


class GameWindow:
    """Base game window instance"""

    # Path to game's icon
    icon_path = None

    # This will ensure game doesnt run faster than 60fps
    clock_speed: int = 60

    # Pygame proxies
    mouse = pygame.mouse
    window = pygame.display

    assets = None
    tree = None
    event_handler = None
    camera = None

    def __init__(self, title: str = "My Game"):
        log.debug("Initializing pygame")
        pygame.init()

        self.title = title
        # This is set from custom init
        self.initialized = False
        self.settings = SettingsManager()
        self.active = False

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
        # Configure is separate function, coz we may want to run it while game
        # is already active, to change stuff (say, from settings menu)
        self.configure()

        # Setting game's icon, if available. This should be done after configuration
        if self.icon_path:
            try:
                i = pygame.image.load(self.icon_path).convert()
            except Exception as e:
                log.warning(f"Unable to set icon: {e}")
                self.icon = None
            else:
                self.icon = i
                self.window.set_icon(self.icon)

        WGF.game = self
        # Scene tree
        if not self.tree:
            self.tree = SceneTree()

        if not self.camera:
            self.camera = Camera()
        WGF.camera = self.camera

        WGF.tree = self.tree
        WGF.clock = self.clock

        from WGF.tasks import TaskManager

        self.task_mgr = TaskManager()

        WGF.task_mgr = self.task_mgr

        self.initialized = True

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
                mode = getattr(WindowMode, f, None)
                if mode is not None:
                    flags.append(mode.value)
        flags = reduce(ior, flags)

        # Game's screen canvas. Its size is the actual size of window.
        # Mostly internal thing to measure background size
        self.screen = self.window.set_mode(
            size=self.settings["size"],
            vsync=self.settings["vsync"],
            flags=flags,
        )

        log.debug(f"Window's settings has been set to {self.settings}")

    def exit(self):
        self.active = False
        log.info("Closing the game. Bye :(")
        pygame.quit()

    def run(self):
        """Run the updater routine. Can only be used once"""
        if not self.initialized:
            log.warning("Unable to run game - GameWindow is not initialized")
            return

        self.active = True
        # while True:
        while self.active:
            self.clock.tick(self.clock_speed)
            # Keep in mind that this instance of task manager runs each frame.
            # If there is custom pause implementation that require manager to be
            # paused, its encouraged to create new one on local scene's level
            self.task_mgr.update()
            self.event_handler.update()
            for event in self.event_handler.events:
                if event.type == pgl.QUIT:
                    # self.exit()
                    return
            self.tree.update()
            # This will update whats visible on screen to player
            self.window.flip()

        self.exit()
