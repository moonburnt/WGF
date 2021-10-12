import logging
from WGF.common import *
from WGF.loader import AssetsLoader
from WGF.base import GameWindow

log = logging.getLogger(__name__)

# Shared variables storage. Similar to flasks's g
class Shared:
    def __repr__(self):
        return f"{self.__name__}: ({vars(self)})"


shared = Shared()
