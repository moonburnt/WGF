from WGF import clock
from pygame import transform, sprite
from enum import Enum
from collections import namedtuple
import logging

log = logging.getLogger(__name__)

# Tasks that require game's clock tickin'


class TaskStatus(Enum):
    stopped = 0
    paused = 1
    active = 2


class Timer:
    """Basic timer that should be updated each frame by task manager"""

    def __init__(self, ms: int):
        # Ensuring no negative values can be passed
        ms = ms if ms >= 0 else 0
        self.time_left = ms
        self._time = ms
        self.status = TaskStatus.active
        self.completion = False

    def update(self) -> bool:
        if self.status is not TaskStatus.active:
            return self.completion

        self.time_left -= clock.get_time()
        if self.time_left <= 0:
            self.status = TaskStatus.stopped
            self.completion = True
        return self.completion

    def reset(self):
        self.time_left = self._time
        self.completion = False

    def restart(self):
        self.reset()
        self.status = TaskStatus.active


class Task:
    """Basic task that does some stuff each frame"""

    def __init__(
        self,
        name: str,
        task_method: callable,
        task_args: list = None,
        task_kwargs: dict = None,
        repeat: bool = True,
        stop_condition=None,
    ):
        self.name = name
        self.task_method = task_method
        self.task_args = task_args or []
        self.task_kwargs = task_kwargs or {}
        self.status = TaskStatus.active
        self.stop_condition = stop_condition
        self.repeat = repeat

    def update(self):
        if self.status is not TaskStatus.active:
            return

        answ = self.task_method(*self.task_args, **self.task_kwargs)
        if (
            not self.repeat
            or self.stop_condition is not None
            and answ == self.stop_condition
        ):
            self.status = TaskStatus.stopped
        return answ

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
        task_args: list = None,
        task_kwargs: dict = None,
        repeat: bool = True,
        stop_condition=None,
    ):
        self.timer = Timer(speed)
        super().__init__(
            name=name,
            task_method=task_method,
            task_args=task_args,
            task_kwargs=task_kwargs,
            repeat=repeat,
            stop_condition=stop_condition,
        )

    def update(self):
        if self.status is not TaskStatus.active:
            return

        if not self.timer.update():
            return
        self.timer.restart()

        answ = self.task_method(*self.task_args, **self.task_kwargs)
        if (
            not self.repeat
            or self.stop_condition is not None
            and answ == self.stop_condition
        ):
            self.status = TaskStatus.stopped
        return answ


ScheduledMethod = namedtuple("ScheduledMethod", ["timer", "func", "args", "kwargs"])


class TaskManager:
    """Task manager"""

    def __init__(self, remove_complete: bool = False):
        # Doing it in init, coz otherwise these will leak to different instances
        self.tasks = {}
        self.remove_complete = remove_complete
        # Queue for nameless stuff thats scheduled to be complete later
        self.queue = []

    def update(self):
        """Perform all tasks assigned to this manager"""

        for t in self.tasks:
            task = self.tasks[t]
            task.update()
            if self.remove_complete and task.status is TaskStatus.stopped:
                self.tasks.pop(t)

        if self.queue:
            copy = self.queue.copy()
            for q in self.queue:
                if q.timer.update():
                    q.func(*q.args, **q.kwargs)
                    copy.remove(q)
            self.queue = copy

    def remove_complete(self):
        """Remove tasks with their status set to TaskStatus.stopped"""

        for t in self.tasks:
            if self.tasks[t].status is TaskStatus.stopped:
                self.tasks.pop(t)

    def do_later(self, ms: int):
        def wrapper(func):
            def inner(*args, **kwargs):
                task = ScheduledMethod(Timer(ms), func, args, kwargs)
                self.queue.append(task)

            return inner

        return wrapper

    def task(self, name: str, repeat: bool = True, stop_condition=None):
        def wrapper(func):
            def inner(*args, **kwargs):
                task = Task(
                    name=name,
                    task_method=func,
                    task_args=args,
                    task_kwargs=kwargs,
                    stop_condition=stop_condition,
                    repeat=repeat,
                )
                self.tasks[name] = task
                # return self.tasks[name].update()

            return inner

        return wrapper

    def timed_task(
        self, name: str, speed: int, repeat: bool = True, stop_condition=None
    ):
        def wrapper(func):
            def inner(*args, **kwargs):
                task = TimedTask(
                    name=name,
                    speed=speed,
                    task_method=func,
                    task_args=args,
                    task_kwargs=kwargs,
                    stop_condition=stop_condition,
                    repeat=repeat,
                )
                self.tasks[name] = task
                # return self.tasks[name].update()

            return inner

        return wrapper


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
        self.timer = Timer(speed)

    def __iter__(self):
        for var in self.sprites:
            yield var

    def __getitem__(self, key: int):
        return self.sprites[key]

    def update(self):
        if not self.timer.update():
            return None
        self.timer.restart()

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
