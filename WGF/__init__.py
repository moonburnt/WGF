import logging
from WGF.common import *
from WGF.loader import AssetsLoader
from WGF.scene import Scene
from WGF.base import GameWindow

log = logging.getLogger(__name__)

# Current game's context. Similar to flask's current_app
game = None

# Current game's tree, which will be later used for easy access to branch operations
tree = None

# Shared variables storage. Similar to flasks's g
class Shared:
    def __repr__(self):
        return f"{self.__name__}: ({vars(self)})"


shared = Shared()

# #TODO: maybe add globally accessible thing for events and configs?
