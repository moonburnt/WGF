import logging

log = logging.getLogger(__name__)


class Scene:
    """Scene template that attaches to SceneTree"""

    _initmethod: callable = None
    _showmethod: callable = None
    _hidemethod: callable = None

    def __repr__(self):
        return f"{type(self).__name__}"

    def __init__(self, name: str):
        self.name = name
        self.tasks = {}
        self.current_task = None
        self.default_task = None
        self.initialized = False

    def run(self):
        """Initialize and run the scene"""

        if not self.initialized:
            self.init()
            self.initialized = True
        self.show()
        if self.default_task:
            self.current_task = self.default_task
        self.update()

    def update(self) -> bool:
        """Run self.current_task if set.
        Meant to be called each frame. Returns completion status.
        """

        if self.current_task:
            self.current_task()
            return True
        return False

    def init(self) -> bool:
        """Run method set with @self.initmethod, if available.
        Meant to be as single-use scene initializer. Returns completion status.
        """

        if self._initmethod:
            self._initmethod()
            return True
        return False

    def show(self) -> bool:
        """Run method set with @self.showmethod, if available.
        Meant to be used each time scene tree switches to this scene.
        Returns completion status.
        """

        if self._initmethod:
            self._initmethod()
            return True
        return False

    def hide(self) -> bool:
        """Run method set with @self.hidemethod, if available.
        Meant to be used when scene tree switches to another scene.
        Returns completion status.
        """

        if self._hidemethod:
            self._hidemethod()
            return True
        return False

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

    def hidemethod(self, func):
        def inner():
            self._hidemethod = func
            return self._hidemethod()

        return inner()

    # Tasks are things that run each frame within current scene's context
    def task(self, name: str, default: bool = False):
        def inner(func):
            self.tasks[name] = func
            if default:
                self.default_task = self.tasks[name]

            def wrapper(*args, **kwargs):
                return self.tasks[name](*args, **kwargs)

            return wrapper

        return inner

    # TODO: maybe distinguish stop and pause? And make it dont actually hide
    # scene, but pause its execution?
    def stop(self):
        self.hide()


class SceneTree:
    """Basic scene graph to organize things inside GameWindow"""

    current: Scene = None
    previous: Scene = None

    scenes: dict = {}

    def __init__(self):
        log.debug("Initializing scene tree")

        self.current: Scene = None
        self.previous: Scene = None
        self.default: Scene = None

        scenes: dict = {}

    def __repr__(self):
        return f"{type(self).__name__}: {self.scenes}"

    def __setitem__(self, key, value):
        # For now only accepting scenes, not its relatives #TODO
        if type(value) is not Scene:
            raise TypeError(f"value must be Scene, not {type(value).__name__}")
        else:
            self.scenes[key] = value

    def __getitem__(self, key):
        return self.scenes[key]

    def add(self, scene: Scene, name: str = None, default: bool = False):
        name = name or getattr(scene, "name")
        self[name] = scene
        # I know its bad to overshadow things like that, but cant find a better
        # name :/ #TODO
        if default:
            self.default = name

    # Current realisation keep state of scene, unlike I did in a2s3.
    # It may cause issues and may need rework #TODO
    def switch(self, name: str):
        """Switch to specific scene"""

        scene = self[name]
        if self.current:
            self.current.stop()
            self.previous = self.current
        self.current = scene
        self.current.run()
        log.debug(f"{type(self).__name__} switched to scene '{name}'")

    def show_previous(self):
        """Show previous scene, if available"""

        if not self.previous:
            log.warning(f"There are no previous scenes in {type(self).__name__}")
            return
        if self.current:
            self.current.stop()
        self.current, self.previous = self.previous, self.current
        self.current.run()
