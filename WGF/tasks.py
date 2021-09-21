from WGF import clock
from pygame import transform, sprite
from enum import Enum
import logging

log = logging.getLogger(__name__)

# Tasks that require game's clock tickin'


class TaskStatus(Enum):
    stopped = 0
    paused = 1
    active = 2


class Task:
    """Basic task that does some stuff each frame"""

    def __init__(
        self,
        name: str,
        task_method: callable,
        task_args: list = [],
        stop_condition=None,
    ):
        self.name = name
        self.task_method = task_method
        self.task_args = task_args
        self.status = TaskStatus.active
        self.stop_condition = stop_condition

    def update(self):
        if self.status is not TaskStatus.active:
            return

        args = []
        answ = self.task_method(*self.task_args)
        self.task_args = args.extend(answ) if answ is not None else args
        if self.stop_condition is not None and self.task_args == self.stop_condition:
            self.status = TaskStatus.stopped
        return self.task_args

    def stop(self):
        self.status = TaskStatus.stopped

    def pause(self):
        self.status = TaskStatus.paused


class TimedTask(Task):
    """Task that only triggers once per specified amount of time"""

    def __init__(
        self,
        name: str,
        task_method: callable,
        speed: int,
        task_args: list = [],
        stop_condition=None,
    ):
        self.speed = speed
        self.time = speed
        super().__init__(name, task_method, task_args, stop_condition)

    def update(self):
        if self.status is not TaskStatus.active:
            return

        self.time -= clock.get_time()
        if self.time <= 0:
            self.time = self.speed
        else:
            return

        args = []
        answ = self.task_method(*self.task_args)
        self.task_args = args.extend(answ) if answ is not None else args
        if self.stop_condition is not None and self.task_args == self.stop_condition:
            self.status = TaskStatus.stopped
        return self.task_args


class TaskManager:
    """Task manager"""

    def __init__(self):
        # Doing it in init, coz otherwise these will leak to different instances
        self.tasks = {}

    def update(self):
        for t in self.tasks:
            self.tasks[t].update()

    def task(self, name: str, stop_condition=None):
        def wrapper(func):
            def inner(*args):
                task = Task(
                    name=name,
                    task_method=func,
                    task_args=args,
                    stop_condition=stop_condition,
                )
                self.tasks[name] = task
                return self.tasks[name].update()

            return inner

        return wrapper

    def timed_task(self, name: str, speed: int, stop_condition=None):
        def wrapper(func):
            def inner(*args):
                task = TimedTask(
                    name=name,
                    speed=speed,
                    task_method=func,
                    task_args=args,
                    stop_condition=stop_condition,
                )
                self.tasks[name] = task
                return self.tasks[name].update()

            return inner

        return wrapper


# def do_later(task: callable, time:int):
#    """Do some task after specified amount of time"""


class Animation:
    """Animation consisting of multiple sprites"""

    # #TODO: add storage to keep flipped sprites

    def __init__(
        self,
        sprites: list,
        loop: bool = True,
        default_frame: int = 0,
        scale: int = None,
        speed: float = 160,
    ):

        if scale:
            # This will fail if size of sprites is not the same
            x, y = sprites[0].get_size()
            x = x * scale
            y = y * scale
            sprites = [transform.scale(img, (x, y)) for img in sprites]

        self.sprites = sprites
        self.loop = loop
        self.current_frame = default_frame
        self.speed = speed

        self._time = speed

    def __iter__(self):
        for var in self.sprites:
            yield var

    def __getitem__(self, key: int):
        return self.sprites[key]

    def next(self):
        self._time -= clock.get_time()
        if self._time <= 0:
            self._time = self.speed
        else:
            return None
        if self.current_frame == len(self.sprites):
            if not self.loop:
                return None
            else:
                self.current_frame = 0

        img = self.sprites[self.current_frame]
        self.current_frame += 1
        return img

    def flip(self, horizontally: bool = False, vertically: bool = False):
        if horizontally or vertically:
            self.sprites = [
                transform.flip(spr, horizontally, vertically) for spr in self.sprites
            ]
