import json
import os
from typing import Any, Callable, Dict, List, Literal

import dotenv
dotenv.load_dotenv()


def _require_env(variable: str) -> str:
    env = os.getenv(variable)
    if env is None:
        raise RuntimeError(f"environment variable {variable} missing")
    return env


def _require_keys(d: Dict[str, Any], keys: List[str]) -> None:
    for key in keys:
        if key not in d:
            raise RuntimeError(f"required key {key} not in {d}")


# for fun, there isn't much point to using something
# other than a quadratic unless you want something
# really funky in which case you should just write
# code instead of json files
def _get_expansion_function(
    degree: int,
    coeffs: List[float],
    start: List[int],
    end: List[int],
) -> Callable[[int], int]:
    if len(coeffs) < degree-1:
        raise RuntimeError(f"not enough coeffs ({len(coeffs)}) for expansion function of degree {degree} (expected {degree-1})")
    if len(coeffs) > degree-1:
        print(f"too many coeffs ({len(coeffs)}) for expansion function of degree {degree} (expected {degree-1}) ignoring excess")
    if len(start) < 2 or len(end) < 2:
        raise RuntimeError("invalid start/end points (points of form (expansionCount, imageSize))")

    if degree == 0:
        return lambda expansion_count: start[1]

    coeffs.append(
        (
            end[1]
            - sum(
                coeffs[i]*(end[0]**(degree-i))
                for i in range(degree-1)
            )
            - start[1]
        )
        / end[0]
    )
    coeffs.append(start[1])

    table = []
    for x in range(start[0], end[0]):
        # synthetic division go brr
        cur = coeffs[0]
        for i in range(1, degree+1):
            cur = cur*x + coeffs[i]
        table.append(round(cur))

    def get_size(expansion_count: int) -> int:
        if expansion_count <= start[0]:
            return start[1]
        if expansion_count >= end[0]:
            return end[1]
        return table[expansion_count-start[0]]

    return get_size


_FormatName = str
_FormatKeys = Literal["maxsize", "format", "reduce", "args"]
_Format = List[Dict[_FormatKeys, Any]]


class _Config(object):
    """Bot configuration, allowing for reloading without restarting code

    All attributes are obtained or derived from environment variables.

    Attributes:
        discord_token (str): Token for the Discord API, for logging
            in. Never reloaded.
            Env: DISCORD_BOT_TOKEN
            Mandatory.
        bot_owner (int): The Discord ID of the user with permission
            to issue the reload command which calls conf.update()
            Env: BOT_OWNER
            Mandatory.
        translation_file (str): Path to a copy of or file similar to
            https://github.com/Aceship/AN-EN-Tags/blob/master/json/tl-akhr.json
            Env: TRANSLATION_FILE
            Mandatory.
        character_list_file (str): Path to a copy of or file similar to
            https://github.com/Aceship/AN-EN-Tags/blob/master/json/gamedata/zh_CN/gamedata/excel/character_table.json
            Env: CHARACTER_LIST_FILE
            Mandatory.
        image_path (str): Path to a folder containing all the images
            to be used in the game, such as the output of
            image_formatter.py or a copy of
            https://github.com/Aceship/AN-EN-Tags/tree/master/img/characters
            Env: IMAGE_PATH
            Mandatory.
        file_name (str): The name of all the images uploaded to
            discord, without an extension.
            Env: FILE_NAME
            Default: "canned_thighs"
        preload_images (bool): Non-lazy loading of images. Pillow
            doesn't read image files until the image is actually used
            in code, which means the bot will slowly increase memory
            usage as more operators are shown. If you want to load
            all the images at the start, set this variable to
            anything. Leaving it unset or set to an empty string
            means that Pillow should lazy-load the images. Note that
            since images are decompressed, RAM usage is likely to be
            a lot higher than the total size on disk of the image
            folder.
            Env: PRELOAD_IMAGES
            Default: False

        The following are controlled by the environment variable
        GAMEDATA_PATH, which is a path to a folder containing the
        files name_aliases.json, image_setup.json, formats.json, and
        game_settings.json, defaulting to "gamedata" (in the current
        directory):

        alias_file (str): The path to the json file containing
            operator aliases, aka valid words/phrases that will be
            accepted as equivalent to the full name by the game.
        image_setup_file (str): The path to the json file containing
            data to be used by image_setup.py, such as images to
            exclude from the game.
        file_formats (Dict[_FormatName, _Format]): The path to the
            json file containing image encoding and compression
            formats to use when sending images to discord.
            Keys:
                maxsize: The upper limit of resolution to apply this
                    sub-format to. Used to have different compression
                    levels on smaller/larger images. The last sub-
                    format within the format should end with maxsize
                    set to -1 (to apply to images of any size not
                    already specified).
                format: The image file format to use, e.g. webp, png.
                reduce: The integer factor to downscale the image by,
                    e.g. 1 to keep resolution, 2 to halve the image's
                    dimensions (quarter the area), etc.
                args: Arguments to provide to the image writer. See
                    https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
                    to find lists of what arguments can be provided
                    when saving each type of image. Can be used to
                    specify levels of compression on formats like png
                    and webp.

        The following are loaded from game_settings.json:

        get_size (Callable[[int], int]): The function to use when
            expanding images in rounds. Outputs the size of the image
            to be created for a certain number of expansion requests.
        expansion_equation (Dict[str, Union[int, List[float]]]): The
            polynomial to use for get_size().
            Keys:
                degree: the degree of the polynomial.
                coeffs: a list of degree-1 numbers, starting from the
                    leading coefficient to the third last coeff.
                end: the coordinates of the last expansion point,
                    (the final size) used to determine the second
                    last coefficient.
                start: the coordinates of the first expansion point
                    (the initial size) used to determine the last
                    coefficient (the y-intercept).
        default_format (str): The name of a format (in the format
            json file) to use by default, unless a game is created
            with a manually specified name of a format (in the format
            json file).
        default_rounds (int): The default number of rounds a game
            should contain, unless a different number is requested.
        opaque_threshold (float): The minimum percentage of fully
            opaque pixels a starting image needs for it to be sent
            out in the game. Prevents the bot from starting on a
            completely blank image or an image with only a tiny bit
            of content default_rounds The default number of rounds a
            game should contain, unless the game is manually started
            with a different amount.
    """

    __slots__ = (
        "_discord_token",
        "_bot_owner",
        "_translation_file",
        "_character_list_file",
        "_image_path",
        "_file_name",
        "_preload_images",
        "_alias_file",
        "_image_setup_file",
        "_file_formats",
        "_get_size",
        "__dict__",
    )

    def __init__(self):
        self._discord_token: str = _require_env("DISCORD_BOT_TOKEN")
        self.update(True)

    def update(self, reloadImages: bool = False):
        # if an optional environment variable was deleted,
        # it would never be reset by load_dotenv, so we must
        # manually reset them.
        os.environ["FILE_NAME"] = "canned_thighs"
        os.environ["PRELOAD_IMAGES"] = ""
        os.environ["GAMEDATA_PATH"] = "gamedata"

        dotenv.load_dotenv(override=True)
        # mandatory variables
        self._bot_owner: int = int(_require_env("BOT_OWNER"))
        self._translation_file: str = _require_env("TRANSLATION_FILE")
        self._character_list_file: str = _require_env("CHARACTER_LIST_FILE")
        self._image_path: str = _require_env("IMAGE_PATH")

        # optional variables
        self._file_name: str = os.getenv("FILE_NAME", "canned_thighs")

        env = os.getenv("PRELOAD_IMAGES")
        self._preload_images: bool = False if env is None or env == "" else True

        # load data
        gamedata: str = os.getenv("GAMEDATA_PATH", "gamedata")

        self._alias_file: str = os.path.join(gamedata, "name_aliases.json")
        self._image_setup_file: str = os.path.join(gamedata, "image_setup.json")

        with open(os.path.join(gamedata, "formats.json")) as format_file:
            self._file_formats: Dict[_FormatName, _Format] = json.load(format_file)

        with open(os.path.join(gamedata, "game_settings.json")) as settings_file:
            settings: Dict[str, Any] = json.load(settings_file)
        _require_keys(
            settings,
            [
                "expansion_equation",
                "default_format",
                "default_rounds",
                "opaque_threshold",
            ]
        )
        self._get_size = _get_expansion_function(**settings["expansion_equation"])

        self.__dict__.update(**settings)

        if reloadImages:
            print("hi")

    @property
    def discord_token(self):
        return self._discord_token

    @property
    def bot_owner(self):
        return self._bot_owner

    @property
    def translation_file(self):
        return self._translation_file

    @property
    def character_list_file(self):
        return self._character_list_file

    @property
    def image_path(self):
        return self._image_path

    @property
    def file_name(self):
        return self._file_name

    @property
    def preload_images(self):
        return self._preload_images

    @property
    def alias_file(self):
        return self._alias_file

    @property
    def image_setup_file(self):
        return self._image_setup_file

    @property
    def file_formats(self):
        return self._file_formats

    @property
    def get_size(self):
        return self._get_size


conf = _Config()
