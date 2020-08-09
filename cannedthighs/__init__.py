import os
from typing import Callable, Optional, TypeVar

import dotenv
dotenv.load_dotenv()


_T = TypeVar('_T')


def _convert_if_not_none(
    value: Optional[str],
    converter: Callable[[str], _T],
    default: _T,
) -> _T:
    if value is None:
        return default

    return converter(value)


# mandatory variables
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
FILE_FORMAT: str = "webp"  # os.getenv("FILE_FORMAT", "webp") # wip
FILE_NAME: str = f"canned_thighs.{FILE_FORMAT}"

# non-lazy loading of images:
# pillow doesn't read the file until the image is actually used, which
# means the bot will slowly increase memory usage as more operators are
# shown. if you want to load all the images at the start, add a variable
# to the .env file called PRELOAD_IMAGES and set it to anything.
# note that it will take up about 2.8 gigs of ram to preload.

# don't preload if the variable is unset,
# i.e. no .env entry. preload if it exists
_preload_images = os.getenv("PRELOAD_IMAGES")
PRELOAD_IMAGES: bool = False if _preload_images is None else True


# optional game variables
OPAQUE_THRESHOLD: float = _convert_if_not_none(
    os.getenv("OPAQUE_THRESHOLD"),
    float,
    0.5,
)

DEFAULT_ROUNDS: int = _convert_if_not_none(
    os.getenv("DEFAULT_ROUNDS"),
    int,
    5,
)

DEFAULT_SHIFT: float = _convert_if_not_none(
    os.getenv("DEFAULT_SHIFT"),
    float,
    0.15,
)

DEFAULT_COEFF: float = _convert_if_not_none(
    os.getenv("DEFAULT_COEFF"),
    float,
    0.3,
)
