from pygame import image, mixer, transform, Surface, Rect, SRCALPHA
from pygame import font as pgfont
from os import listdir
from os.path import isfile, isdir, basename, join, splitext
from WGF.common import RGB, Size
import logging

log = logging.getLogger(__name__)


# Various things to load media
def get_files(
    path,
    include_subdirs: bool = False,
    extensions: list = None,
    case_insensitive: bool = True,
) -> list:
    """Fetch list of files from provided directory"""
    files = []

    log.debug(f"Attempting to parse directory {path}")
    directory_content = listdir(path)

    if extensions and case_insensitive:
        extensions = [f.lower() for f in extensions]

    for item in directory_content:
        log.debug(f"Processing {item}")
        itempath = join(path, item)
        if isdir(itempath):
            if include_subdirs:
                files += self.get_files(itempath, include_subdirs, extensions)
            continue
        # assuming that everything that isnt directory is file
        if extensions:
            for extension in extensions:
                if case_insensitive:
                    file_ext = splitext(itempath)[-1].lower()
                else:
                    file_ext = splitext(itempath)[-1]

                if file_ext == extension:
                    files.append(itempath)
        else:
            files.append(itempath)

    log.debug(f"Fetched following files from {path}: {files}")
    return files


def _get_storage_name(filename: str) -> str:
    """Turn filename into storage-compatible format"""
    return splitext(basename(filename))[0]


# Idea is the same as in panda3d - we save files into storage under their
# base name without extension
def get_from_files(files: list, loader: callable, loader_kwargs: dict = {}) -> dict:
    """Process provided files with provided loader"""
    data = {}
    for f in files:
        filename = _get_storage_name(f)
        try:
            item = loader(f, **loader_kwargs)
        except Exception as e:
            log.warning(f"Unable to load {item}: {e}")
            continue
        data[filename] = item

    return data


def _is_power_of_two(num) -> bool:
    return num and not (num & (num - 1))


class InvalidSpriteSize(Exception):
    """Exception thrown if requested sprite size doesnt fit spritesheet's size"""

    def __init__(self, size: Size):
        message = f"Spritesheet wont cut into perfect {size} chunks"
        super().__init__(message)


class Spritesheet:
    """Spritesheet holder"""

    def __init__(self, image: Surface):
        self.sprites = {}
        self.image = image

    @classmethod
    def from_file(cls, path, colorkey: RGB = None, has_alpha: bool = True):
        """Get spritesheet from provided path"""

        img = image.load(path)

        if has_alpha and img.get_alpha():
            img = img.convert_alpha()
        else:
            img = img.convert()

        if colorkey is not None:
            img.set_colorkey(colorkey.astuple(), RLEACCEL)

        return cls(img)

    # #TODO: add args to skip some pixels on right/bottom of sheet
    # #TODO: maybe rename it to "to_sprites", since it turns whole img into these?
    def get_sprites(
        self, size: Size, store: bool = True, overwrite_known: bool = False
    ) -> list:
        """Get all sprites of provided size from image, if possible"""

        x, y = size

        img_x, img_y = self.image.get_size()
        if img_x % x or img_y % y:
            raise InvalidSpriteSize(size)

        columns = int(img_x / x)
        rows = int(img_y / y)

        if not _is_power_of_two(columns) or not _is_power_of_two(rows):
            raise InvalidSpriteSize(size)

        items = []
        for row in range(0, rows):
            log.debug(f"Processing row {row}")
            for column in range(0, columns):
                log.debug(f"Processing column {column}")
                sprite_x = column * x
                sprite_y = row * y

                rect = Rect(sprite_x, sprite_y, x, y)
                # print(rect.size)
                if (
                    f"{sprite_x, sprite_y, x, y}" in self.sprites
                    and not overwrite_known
                ):
                    sprite = self.sprites[f"{sprite_x, sprite_y, x, y}"]
                else:
                    if self.image.get_alpha():
                        sprite = Surface(rect.size, SRCALPHA).convert_alpha()
                    else:
                        sprite = Surface(rect.size).convert()
                    sprite.blit(self.image, (0, 0), rect)
                    if store:
                        self.sprites[f"{sprite_x, sprite_y, x, y}"] = sprite

                items.append(sprite)

        return items


# #TODO: rework loaders and storages into things attachable via decorators
class AssetsLoader:
    """Class dedicated to loading assets from disk"""

    def __init__(
        self,
        assets_directory: str,
        images_directory: str = None,
        sounds_directory: str = None,
        fonts_directory: str = None,
        image_extensions: list = None,
        sound_extensions: list = None,
        font_extensions: list = None,
        font_size: int = None,
    ):
        # Path to assets directory
        log.debug("Initializing assets loader")

        self.assets_directory = assets_directory
        self.images_directory = images_directory or assets_directory
        self.sounds_directory = sounds_directory or assets_directory
        self.fonts_directory = fonts_directory or assets_directory

        # Default extensions to seek with loaders of multiple items
        self.image_extensions = image_extensions or []
        self.sound_extensions = sound_extensions or []
        self.font_extensions = font_extensions or []

        # Default font size. Ikr its not best to hardcode values, but whatever
        self.font_size = font_size or 10

        self.clean_all()

    # Single-item getters/loaders have no try/excepts. At least for now
    def get_sound(self, path) -> mixer.Sound:
        """Get sound from provided path"""

        return mixer.Sound(path)

    def load_sound(self, path) -> mixer.Sound:
        """Load sound from provided path into self.sounds"""

        s = self.get_sound(path)
        filename = _get_storage_name(path)
        # No protections/warnings from overwrites for now
        self.sounds[filename] = s

        return s

    def get_sounds(
        self,
        path=None,
        extensions: list = None,
        include_subdirs: bool = False,
        case_insensitive: bool = False,
    ) -> dict:
        """Get sounds from provided path"""

        path = path or self.sounds_directory
        extensions = extensions or self.sound_extensions

        files = get_files(
            path=path,
            extensions=extensions,
            include_subdirs=include_subdirs,
            case_insensitive=case_insensitive,
        )

        # Idea is the same as in panda3d - we save files into storage under their
        # base name without extension
        return get_from_files(files, self.get_sound)

    def load_sounds(
        self,
        path=None,
        extensions: list = None,
        include_subdirs: bool = False,
        case_insensitive: bool = False,
    ) -> dict:
        """Load sounds from provided path into self.sounds"""

        s = self.get_sounds(
            path=path,
            extensions=extensions,
            include_subdirs=include_subdirs,
            case_insensitive=case_insensitive,
        )

        # Python 3.5+ stuff
        self.sounds = {**self.sounds, **s}

        return s

    def get_image(
        self,
        path,
        colorkey: RGB = None,
        has_alpha: bool = True,
        scale: int = None,
    ) -> Surface:
        """Get image from provided path"""

        # This will fail if path is invalid
        img = image.load(path)

        if scale:
            x, y = img.get_size()
            x = x * scale
            y = y * scale
            img = transform.scale(img, (x, y))

        if has_alpha and img.get_alpha():
            img = img.convert_alpha()
        else:
            img = img.convert()

        # This will set specific color to act as alpha channel
        # #TODO: idk if this will work with existing alpha tho
        if colorkey is not None:
            img.set_colorkey(colorkey.astuple(), RLEACCEL)

        return img

    def load_image(
        self,
        path,
        colorkey: RGB = None,
        has_alpha: bool = True,
        scale: int = None,
    ) -> Surface:
        """Load image from provided path into self.images"""

        img = self.get_image(
            path=path,
            colorkey=colorkey,
            has_alpha=has_alpha,
            scale=scale,
        )
        filename = _get_storage_name(path)
        self.images[filename] = img

        return img

    def get_images(
        self,
        path=None,
        colorkey: RGB = None,
        has_alpha: bool = True,
        scale: int = None,
        extensions: list = None,
        include_subdirs: bool = False,
        case_insensitive: bool = False,
    ) -> dict:
        """Get images from provided path"""

        path = path or self.images_directory
        extensions = extensions or self.image_extensions

        files = get_files(
            path=path,
            extensions=extensions,
            include_subdirs=include_subdirs,
            case_insensitive=case_insensitive,
        )

        kwargs = {
            "colorkey": colorkey,
            "has_alpha": has_alpha,
            "scale": scale,
        }

        return get_from_files(files, self.get_image, loader_kwargs=kwargs)

    def load_images(
        self,
        path=None,
        colorkey: RGB = None,
        has_alpha: bool = True,
        scale: int = None,
        extensions: list = None,
        include_subdirs: bool = False,
        case_insensitive: bool = False,
    ) -> dict:
        """Load images from provided path into self.images"""

        i = self.get_images(
            path=path,
            colorkey=colorkey,
            has_alpha=has_alpha,
            scale=scale,
            extensions=extensions,
            include_subdirs=include_subdirs,
            case_insensitive=case_insensitive,
        )

        self.images = {**self.images, **i}

        return i

    def get_font(
        self,
        path,
        size: int = None,
    ) -> pgfont.Font:
        """Get font from provided path"""

        # Not best to hardcode it, ikr
        size = size or self.font_size
        return pgfont.Font(path, size)

    def load_font(
        self,
        path,
        size: int = None,
    ) -> pgfont.Font:
        """Load font from provided path into self.fonts"""

        f = self.get_font(path, size)
        filename = _get_storage_name(path)
        self.fonts[filename] = f

        return f

    def get_fonts(
        self,
        path=None,
        size: int = None,
        extensions: list = None,
        include_subdirs: bool = False,
        case_insensitive: bool = False,
    ) -> dict:
        """Get fonts from provided path"""

        path = path or self.fonts_directory
        extensions = extensions or self.font_extensions

        files = get_files(
            path=path,
            extensions=extensions,
            include_subdirs=include_subdirs,
            case_insensitive=case_insensitive,
        )

        return get_from_files(files, self.get_font)

    def load_fonts(
        self,
        path=None,
        size: int = None,
        extensions: list = None,
        include_subdirs: bool = False,
        case_insensitive: bool = False,
    ) -> dict:
        """Load fonts from provided path into self.fonts"""

        f = self.get_fonts(
            path=path,
            size=size,
            extensions=extensions,
            include_subdirs=include_subdirs,
            case_insensitive=case_insensitive,
        )

        self.fonts = {**self.fonts, **f}

        return f

    def load_all(self):
        """Load all valid media from provided paths into relevant storages"""

        self.load_images()
        self.load_sounds()
        self.load_fonts()

    def clean_all(self):
        """Clean all local storages"""

        self.images = {}
        self.sounds = {}
        self.fonts = {}
