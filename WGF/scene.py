import logging

log = logging.getLogger(__name__)

__all__ = [
    "Scene",
    "SceneTree",
]


class Scene:
    """Scene template that attaches to SceneTree"""

    _parent = None
    _childs: dict = {}
    _current_child = None
    _default_child = None

    _initmethod: callable = None
    _showmethod: callable = None
    _hidemethod: callable = None
    _updatemethod: callable = None
    _pausemethod: callable = None

    def __repr__(self):
        return f"{type(self).__name__}"

    def __setitem__(self, key, value):
        # For now only accepting scenes, not their relatives #TODO
        if type(value) is not Scene:
            raise TypeError(f"value must be Scene, not {type(value).__name__}")
        else:
            self._childs[key] = value

    def __getitem__(self, key):
        return self._childs[key]

    def __init__(self, name: str):
        self.name = name
        self.initialized = False
        self.shown = False
        self.playing = False
        self.first_run = True

    # These decorators will check if related functions has been used and perform
    # them, if not
    def require_init(func):
        def inner(self, *args, **kwargs):
            self.init()
            return func(self, *args, **kwargs)

        return inner

    def require_show(func):
        def inner(self, *args, **kwargs):
            self.show()
            return func(self, *args, **kwargs)

        return inner

    def require_hide(func):
        def inner(self, *args, **kwargs):
            self.hide()
            return func(self, *args, **kwargs)

        return inner

    def init(self):
        """Run method set with @self.initmethod, if available.
        Meant to be as single-use scene initializer.
        """
        if self.initialized:
            return

        # idk if it should be there or below
        if self._default_child:
            self._current_child = self._default_child

        if self._initmethod:
            self._initmethod()
            self.initialized = True

    # I think it should only require init, coz we will probably use this as go-to
    # solution to run self.update(), and some scenes may work as background tasks.
    # Idk #TODO
    # @require_show
    @require_init
    def play(self):
        """Initialize and run the scene"""
        # I may want to add something like "background_task" bool to scene's init,
        # to toggle this. #TODO
        # Right now the idea is to show scene right away, if its launched for the
        # first time. Idk, may remove later completely in favor of @require_show,
        # coz right now concepts of how different toggles must work has mixed up
        # in my mind. Will see, based on test applications #TODO
        if self.first_run:
            self.show()
            self.first_run = False

        if not self.playing:
            self.update()
            self.playing = True

        if self._current_child:
            self._current_child.play()

    # @require_show
    def update(self):
        """Run method set with @self.updatemethod, if available.
        Meant to be called each frame by scene tree, while scene is active.
        Returns completion status.
        """

        if self.playing:
            if self._updatemethod:
                self._updatemethod()
            if self._current_child:
                self._current_child.update()

    @require_init
    def show(self) -> bool:
        """Run method set with @self.showmethod, if available.
        Meant to be used each time scene tree switches to this scene.
        Returns completion status.
        """
        if self.shown:
            return True

        if self._showmethod:
            self._showmethod()
            self.shown = True
            return True
        return False

    def hide(self) -> bool:
        """Run method set with @self.hidemethod, if available.
        Meant to be used when scene tree switches to another scene.
        Returns completion status.
        """

        if not self.shown:
            return True

        if self._hidemethod:
            self._hidemethod()
            self.shown = False
            return True
        return False

    # None of these accept function arguments, for now. Because I couldnt think
    # of how to handle them from scene tree's point #TODO
    def initmethod(self, func):
        def inner():
            self._initmethod = func
            return self._initmethod()

        return inner()

    def showmethod(self, func):
        def inner():
            self._showmethod = func
            return self._showmethod()

        return inner()

    def updatemethod(self, func):
        def inner():
            self._updatemethod = func
            return self._updatemethod()

        return inner()

    def hidemethod(self, func):
        def inner():
            self._hidemethod = func
            return self._hidemethod()

        return inner()

    def pausemethod(self, func):
        def inner():
            self._pausemethod = func
            return self._pausemethod()

        return inner()

    def add(self, scene, name: str = None, default: bool = False):
        name = name or getattr(scene, "name")
        self[name] = scene
        if default:
            # maybe only keep name? #TODO
            self._default_child = self[name] = scene

    def pause(self):
        """Pause scene's update() from playing.
        Additionally runs method set with @pausemethod, if available"""

        if not self.playing:
            return

        # Unlike some other functions, this isnt requirement - this method will
        # just add stuff on top (say, if we need to show some text), but dont
        # rework actual pause behavior
        if self._pausemethod:
            self._pausemethod()
        self.playing = False

    # Idk if this needs hide() or not #TODO
    def stop(self):
        """Pause scene's playback and reset initialization state"""

        self.pause()
        self.initialized = False
        # self.hide()


class SceneTree(Scene):
    def __init__(self):
        super().__init__(name="Root")

    def switch(self, name: str):
        """Switch to specific scene"""

        scene = self[name]
        if self._current_child:
            self._current_child.stop()
            # self.previous = self.current
        self._current_child = scene
        self._current_child.play()
        log.debug(f"{type(self).__name__} switched to scene '{name}'")
