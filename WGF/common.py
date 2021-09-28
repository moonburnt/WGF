from dataclasses import dataclass, astuple, asdict

import logging

log = logging.getLogger(__name__)

# Various common types to use across application

__all__ = [
    "RGB",
    "Size",
    "Point",
]

# This is a base for other dataclasses that need to have their internal conversion
# methods and intended to be used where pygame expects tuple or list (for bettter
# typehints, additional methods and other funny stuff).
# Its kinda jank tho, due to how DC inheritance works
class ConvertableType:
    # This will break default conversion to dict, but instead will represent type's
    # iteration in list/tuple-like way
    def __iter__(self):
        for var in vars(self):
            yield getattr(self, var)

    # And this makes it possible to fetch values from type in both list-like and
    # dict-like fashion, depending on type of key. This is kinda slow tho
    def __getitem__(self, key):
        if type(key) is int:
            return astuple(self)[key]
        elif type(key) is str:
            return vars(self)[key]
        else:
            raise TypeError(f"key must be int or str, not {type(key).__name__}")

    # Support for len(cls). May be required in some places that expect tuple-like
    # or list-like behavior
    def __len__(self):
        return len(vars(self))

    # This is garbage, but I didnt find a better solution to dont require carrying
    # this around and to keep ability to convert dataclass to dict.

    # Names of converters are inspired by methods of Pandas Dataframes
    def to_tuple(self):
        return astuple(self)

    def to_dict(self):
        return asdict(self)


def clamp(val, minval, maxval):
    """Get value in between provided range"""

    return max(min(maxval, val), minval)


@dataclass(frozen=True)
class RGB(ConvertableType):
    red: int = 0
    green: int = 0
    blue: int = 0

    # Ensuring our values will remain in valid RGB range
    def __post_init__(self):
        items = vars(self)
        for i in items:
            object.__setattr__(self, i, clamp(items[i], 0, 255))

    @classmethod
    def from_hex(cls, color: str):
        """Create RGB color from provided hex color"""
        if color.startswith("#"):
            color = color[1:]

        # if len(color) < 6:
        if len(color) != 6:
            raise ValueError(color)

        r = int(f"0x{color[0]}{color[1]}", 0)
        g = int(f"0x{color[2]}{color[3]}", 0)
        b = int(f"0x{color[4]}{color[5]}", 0)

        return cls(r, g, b)

    def to_hex(self) -> str:
        hx = "#"
        for color in (self.red, self.green, self.blue):
            hx += "%02x" % color
        return hx


@dataclass(frozen=True)
class RGBA(RGB):
    alpha: int = 255


# Size is used for abstract height and width values
@dataclass(frozen=True)
class Size(ConvertableType):
    width: int
    height: int


# While point is used to reffer to some specific x, y location on screen
# @dataclass(frozen=True)
@dataclass
class Point(ConvertableType):
    x: int
    y: int
