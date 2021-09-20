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

    def __init__(self, name: str, task_method: callable, task_args: tuple = tuple()):
        self.name = name
        self.task_method = task_method
        self.task_args = task_args
        self.status = TaskStatus.active

    def update(self):
        if self.status is TaskStatus.active:
            self.task_args = self.task_method(*self.task_args)
            return self.task_args

    def stop(self):
        self.status = TaskStatus.stopped

    def pause(self):
        self.status = TaskStatus.paused


# class FiniteTask(Task):
#     """Task that can be interrupted at some point"""

#     def __init__(self, name:str, task_method: callable, repeat: int = -1, task_args: tuple = tuple()):
#         self.name = name
#         self.task_method = task_method
#         self.task_args = task_args
#         self.status = TaskStatus.active

#         # Idea is similar to panda's tasks.
#         # Repeat counter is int that can be from -1 to any positive value
#         self.repeat = repeat

#     def do_task(self):
#         args = self.task_method(*self.task_args)
#         if args:
#             self.repeat = args[0]
#             self.task_args = args[1:]
#         else:
#             self.repeat = 0
#             self.task_args = []
#             self.status = TaskStatus.stopped


class TimedTask(Task):
    """Task that only triggers once per specified amount of time"""

    def __init__(
        self, name: str, task_method: callable, speed: int, task_args: tuple = tuple()
    ):
        self.speed = speed
        self.time = speed
        super().__init__(name, task_method, task_args)

    def update(self):
        if self.status is not TaskStatus.active:
            return

        self.time -= clock.get_time()
        if self.time <= 0:
            self.time = self.speed
        else:
            return

        self.task_args = self.task_args or tuple()
        self.task_args = self.task_method(*self.task_args)
        return self.task_args


class TaskManager:
    """Task manager"""

    def __init__(self):
        # Doing it in init, coz otherwise these will leak to different instances
        self.tasks = {}

    def update(self):
        for t in self.tasks:
            self.tasks[t].update()

    def task(self, name: str):
        def wrapper(func):
            def inner(*args):
                task = Task(
                    name=name,
                    task_method=func,
                    task_args=args,
                )
                self.tasks[name] = task
                return self.tasks[name].update()

            return inner

        return wrapper

    def timed_task(self, name: str, speed: int):
        def wrapper(func):
            def inner(*args):
                task = TimedTask(
                    name=name,
                    speed=speed,
                    task_method=func,
                    task_args=args,
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
