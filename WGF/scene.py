import logging

log = logging.getLogger(__name__)


class Scene:
    """Scene template that attaches to SceneTree"""

    def __repr__(self):
        return f"{type(self).__name__}"

    def __init__(self, name: str):
        self.name = name
        self.tasks = {}
        self.current_task = None
        self.default_task = None
        self.initialized = False

    def run(self):
        if not self.initialized:
            self.init()
            self.initialized = True
        self.show()
        if self.default_task:
            self.current_task = self.default_task
        self.update()

    def update(self):
        if self.current_task:
            self.current_task()

    def show(self, func=None):
        func = func or self.show
        self.show = func

        def inner():
            return func()

        return inner

    # Custom init, where you write your stuff
    # Im not sure about how this and show works :/
    def init(self, func=None):
        func = func or self.init
        self.init = func

        def inner():
            return func()

        return inner

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

    def stop(self):
        self.hide()

    # This runs when you need to switch to other scene. Usually cleanup stuff
    def hide(self):
        pass


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
