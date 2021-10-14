from WGF import camera, Point, RGB, game, tree
from WGF.base import NodeBase
from WGF.tasks import Animation
from WGF.common import Counter
from pygame import Surface, font, mouse
from enum import Enum
import logging

log = logging.getLogger(__name__)

# Aligns to be used with some nodes. For now, not everything allowed by pygame
# is implemented - just what Im using personally #TODO
class Align(Enum):
    center = 0
    topleft = 1
    topright = 2


# #TODO: add generic node stuff (path/parent, reparenting etc) to node
# #TODO: add something like show_queue, coz right now showmethod is triggered
# right after adding one node to another, even if its not attached to scenetree
class Node(NodeBase):
    """Base node, from which others should inherit"""

    _parent = None

    _initmethod: callable = None
    _updatemethod: callable = None
    _pausemethod: callable = None
    _showmethod: callable = None
    _hidemethod: callable = None

    def __init__(self, name: str):
        super().__init__(name=name)
        self.active = False
        self.initialized = False
        self.shown = False

    # None of these accept function arguments, for now. Because I couldnt think
    # of how to handle them from scene tree's point #TODO
    def initmethod(self, func):
        def inner():
            self._initmethod = func

        return inner()

    def showmethod(self, func):
        def inner():
            self._showmethod = func

        return inner()

    def updatemethod(self, func):
        def inner():
            self._updatemethod = func

        return inner()

    def hidemethod(self, func):
        def inner():
            self._hidemethod = func

        return inner()

    def pausemethod(self, func):
        def inner():
            self._pausemethod = func

        return inner()

    def init(self):
        """Run method set with @self.initmethod, if available.
        Meant to be as single-use scene initializer.
        """
        if self.initialized:
            return

        if self._initmethod:
            self._initmethod()
        self.initialized = True

    def update(self) -> bool:
        # #TODO: it may be wiser to, instead of doing things recursively,
        # add all initialized and active nodes to game tree's list and iterate
        # tru them there. And when node gets paused - remove it from this list
        if not self.active:
            return False

        for item in self._children.values():
            item.update()

        if self._updatemethod:
            self._updatemethod()
        return True

    def draw(self):
        pass

    def show(self, play: bool = True):
        if self.shown:
            return

        if self._showmethod:
            self._showmethod()
        self.shown = True
        self.active = play

    def play(self):
        self.active = True

    def pause(self):
        if self._pausemethod:
            self._pausemethod()
        self.active = False

    def hide(self, pause: bool = True):
        if not self.shown:
            return

        if self._hidemethod:
            self._hidemethod()
        self.shown = False
        self.active = False if pause else True

    def stop(self):
        self.hide()
        self.initialized = False

    def toggle_pause(self):
        if self.active:
            self.active = False
        else:
            self.active = True

    def toggle_hide(self):
        if self.shown:
            self.shown = False
        else:
            self.shown = True


class VisualNode(Node):
    def __init__(
        self,
        name: str,
        surface: Surface,
        pos: Point,
        distance: float = 0.0,
        align: Align = Align.center,
    ):
        self.surface = surface
        self.rect = self.surface.get_rect()
        # Distance means distance from camera. Its float that should (under normal
        # circuimstances) be between 0.0 and 1.0.
        # 0.0 means entity's position is unaffected by camera, 1.0 - that it
        # moves together with camera. Its not recommended to set non-default
        # distance to moving targets tho
        self.distance = distance
        self.align = align
        self.pos = pos
        super().__init__(name)

    def update(self) -> bool:
        if super().update():
            if self.distance:
                self.pos = self._pos

            # game.screen.blit(self.surface, self.rect)
            tree.draw_list.append(self)
            return True
        return False

    # #TODO: I may want to check if node is within screen's POV. So if its outside -
    # things will get calculated, but nothing will be redrawn, to reduce resource
    # usage on large maps that heavily utilize camera
    def draw(self):
        game.screen.blit(self.surface, self.rect)

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos: Point):
        self._pos = pos
        if self.align is Align.topleft:
            self.rect.x = int(camera.pos.x * self.distance + self.pos.x)
            self.rect.y = int(camera.pos.y * self.distance + self.pos.y)
        elif self.align is Align.topright:
            self.rect.topright = (
                int(camera.pos.x * self.distance + self.pos.x),
                int(camera.pos.y * self.distance + self.pos.y),
            )
        else:
            self.rect.centerx = int(camera.pos.x * self.distance + self.pos.x)
            self.rect.centery = int(camera.pos.y * self.distance + self.pos.y)

    @property
    def realpos(self):
        return self.rect.get_pos()


# #TODO: add ability to change properties after creation
class TextNode(VisualNode):
    """Node for text messages"""

    def __init__(
        self,
        name: str,
        text: str,
        font: font.Font,
        antialiasing: bool = True,
        pos: Point = None,
        color: RGB = (0, 0, 0),
        frame: Surface = None,
        distance: float = 0.0,
        align: Align = Align.center,
    ):
        self.font = font
        self.antialiasing = antialiasing
        self.color = color

        super().__init__(
            surface=self.font.render(text, self.antialiasing, self.color),
            pos=pos or Point(0, 0),
            distance=distance,
            name=name,
            align=align,
        )

        self.text = text
        self.frame = frame

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text: str):
        self._text = text
        self.surface = self.font.render(self._text, self.antialiasing, self.color)
        self.rect = self.surface.get_rect()
        self.pos = self._pos

    def draw(self):
        if self.frame:
            game.screen.blit(self.frame, self.rect)
        super().draw()


class AnimatedNode(VisualNode):
    """Node that plays provided animation"""

    def __init__(
        self, name: str, animation: Animation, pos: Point, distance: float = 0.0
    ):
        self.animation = animation
        super().__init__(
            surface=self.animation.current_frame,
            pos=pos,
            distance=distance,
            name=name,
        )

    def update(self):
        if super().update(self):
            nxt = self.animation.update()
            if nxt:
                self.surface = nxt
            return True
        return False


class Group(Node):
    """Group of nodes of same type"""

    def __init__(self, name: str):
        self.counter = Counter()
        super().__init__(name=name)

    def add_child(self, node, show: bool = True):
        node.init()
        if show:
            node.show()

        self._children[f"{self.name}_{next(self.counter)}"] = node


class Scene(Node):
    """Node with some static background"""

    def __init__(self, name: str, background: Surface = None):
        self.background = background
        super().__init__(name)

    def update(self) -> bool:
        if not self.active:
            return False

        tree.draw_list.append(self)
        for item in self._children.values():
            item.update()

        if self._updatemethod:
            self._updatemethod()
        return True

    def draw(self):
        game.screen.blit(self.background, (0, 0))


class Cursor(Node):
    """Node that follows the mouse cursor"""

    def __init__(self, name: str, surface: Surface):
        # It inherits from Node and not VisualNode, coz it has no distance
        self.surface = surface
        self.rect = self.surface.get_rect()

        self.pos = mouse.get_pos()
        super().__init__(name)

    def update(self) -> bool:
        if super().update():
            self.pos = mouse.get_pos()

            tree.draw_list.append(self)
            return True
        return False

    def draw(self):
        game.screen.blit(self.surface, self.rect)

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos: Point):
        self._pos = pos
        self.rect.centerx, self.rect.centery = self.pos

    @property
    def realpos(self):
        return self.rect.get_pos()


class Button(TextNode):
    """Simple button, that can be clicked"""

    def __init__(
        self,
        name: str,
        text: str,
        font: font.Font,
        clickmethod: callable = None,
        antialiasing: bool = True,
        pos: Point = None,
        color: RGB = (0, 0, 0),
        frame: Surface = None,
        distance: float = 0.0,
        align: Align = Align.center,
    ):
        super().__init__(
            name=name,
            text=text,
            font=font,
            antialiasing=antialiasing,
            pos=pos,
            color=color,
            frame=frame,
            distance=distance,
            align=align,
        )
        self._clickmethod = clickmethod

    def clickmethod(self, func):
        def inner():
            self._clickmethod = func

        return inner()

    def on_click(self):
        if self._clickmethod:
            self._clickmethod()
