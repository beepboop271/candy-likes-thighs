import json
import os
from typing import Any, Callable, Dict, List, Literal, TypeVar

import dotenv
dotenv.load_dotenv()


_T = TypeVar('_T')


def _get_env(
    key: str,
    converter: Callable[[str], _T],
    default: _T,
) -> _T:
    setting = os.getenv(key)

    if setting is None:
        return default

    try:
        return converter(setting)
    except ValueError:
        print(f"could not convert {key}={setting}, using default {default}")
        return default


# mandatory variables
#
# DISCORD_BOT_TOKEN
# Self-explanatory, used to log in
#
# DATA_PATH
# Relative or absolute path to the folder containing
# a clone of https://github.com/Aceship/AN-EN-Tags or
# just a folder structured the same way containing
# only the necessary files
#
_token = os.getenv("DISCORD_BOT_TOKEN")
if _token is None:
    raise RuntimeError("no discord token found")

_data_path = os.getenv("DATA_PATH")
if _data_path is None:
    raise RuntimeError("no data path specified")

# mypy is bad at type checking
DISCORD_BOT_TOKEN: str = _token

DATA_PATH: str = _data_path


# optional bot variables
#
# FILE_NAME
# The name of all the images uploaded to discord,
# without an extension
# Default: canned_thighs
#
# ALIAS_PATH
# The path to the json file containing operator
# aliases, aka valid words/phrases that will be
# accepted as equivalent to the full name by the game
# Default: name_aliases.json (in current directory)
#
# FORMAT_PATH
# The path to the json file containing image encoding
# formats to use when sending images to discord
# Default: formats.json (in current directory)
#
# PRELOAD_IMAGES
# Non-lazy loading of images. Pillow doesn't read
# image files until the image is actually used in
# code, which means the bot will slowly increase
# memory usage as more operators are shown. If you
# want to load all the images at the start, set this
# variable to anything. Leaving it unset means that
# Pillow should lazy-load the images. Note that it
# will take up about 2.8 gigs of ram to preload
#
FILE_NAME: str = os.getenv("FILE_NAME", "canned_thighs")

ALIAS_FILE_PATH: str = os.getenv("ALIAS_PATH", "name_aliases.json")

IMAGE_SETUP_PATH: str = os.getenv("SETUP_PATH", "image_setup.json")

_FORMAT_FILE_PATH: str = os.getenv("FORMAT_PATH", "formats.json")
_FormatName = str
_FormatKeys = Literal["maxsize", "format", "reduce", "args"]
_Format = List[Dict[_FormatKeys, Any]]
with open(_FORMAT_FILE_PATH) as format_file:
    FILE_FORMATS: Dict[_FormatName, _Format] = json.load(format_file)


PRELOAD_IMAGES: bool = False if os.getenv("PRELOAD_IMAGES") is None else True


# optional game variables
#
# DEFAULT_FORMAT
# The name of a format (in the format json file) to
# use by default, unless a game is created with a
# manually specified name of a format (in the format
# json file)
# Default: optimized
#
# OPAQUE_THRESHOLD
# The minimum percentage of fully opaque pixels a
# starting image needs for it to be sent out in the
# game. Prevents the bot from starting on a
# completely blank image or an image with only a tiny
# bit of content
# Default: 0.5
#
# DEFAULT_ROUNDS
# The default number of rounds a game should contain,
# unless the game is manually started with a
# different amount
# Default: 5
#
# DEFAULT_SHIFT
# The default constant used in the image expansion
# formula, unless the game is manually started with a
# different shift
# Default: 0.15
#
# DEFAULT_COEFF
# The default multiplier used in the image expansion
# formula, unless the game is manually started with a
# different shift
# Default: 0.3
#
DEFAULT_FORMAT = os.getenv("DEFAULT_FORMAT", "optimized")

OPAQUE_THRESHOLD: float = _get_env("OPAQUE_THRESHOLD", float, 0.5)

DEFAULT_ROUNDS: int = _get_env("DEFAULT_ROUNDS", int, 5)

DEFAULT_SHIFT: float = _get_env("DEFAULT_SHIFT", float, 0.15)

DEFAULT_COEFF: float = _get_env("DEFAULT_COEFF", float, 0.3)
