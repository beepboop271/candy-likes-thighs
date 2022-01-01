# mostly a flask wrapper around
# discord-bot/cannedthighs/__init__.py and
# discord-bot/cannedthighs/image_generator.py

import functools
import io
import json
import os
import pathlib
import random
from typing import Any, Dict, List, Literal, Optional, Tuple
import urllib.parse

import dotenv
from flask import abort, Flask, redirect, request, make_response
from PIL import Image


# loading config #################

dotenv.load_dotenv(".image.env")

# IMAGE_PATH
# Path to a folder containing all the images that
# should be served
IMAGE_PATH = os.getenv("IMAGE_PATH")
if IMAGE_PATH is None:
    raise RuntimeError("path to image data not specified")

# FORMAT_PATH
# The path to the json file containing image encoding
# formats to use when sending images
# Default: formats.json (in current directory)
_FormatName = str
_FormatKeys = Literal["maxsize", "format", "reduce", "args"]
_Format = List[Dict[_FormatKeys, Any]]
with open(os.getenv("FORMAT_PATH", "formats.json")) as format_file:
    FILE_FORMATS: Dict[_FormatName, _Format] = json.load(format_file)

# DEFAULT_FORMAT
# The format from formats.json to use by default,
# unless another is manually requested
DEFAULT_FORMAT = os.getenv("DEFAULT_FORMAT", "optimized")

# DEFAULT_THRESHOLD
# The default required percentage of opaque pixels
# a newly generated image must have before it is sent
DEFAULT_THRESHOLD = float(os.getenv("DEFAULT_THRESHOLD", "0.4"))

# PADDING
# The amount of empty space to ignore around each
# image
PADDING = int(os.getenv("PADDING", "40"))

# MAX_SIZE_THRESHOLD
# The maximum value of size*threshold a request can
# provide in its arguments without being immediately
# refused. Prevents requesting a new image with both
# a large size and a high threshold, which may be
# very difficult, or even impossible to fulfill with
# random means. However, allows requests of small
# images with high threshold or large images with low
# threshold
MAX_SIZE_THRESHOLD = int(os.getenv("MAX_SIZE_THRESHOLD", "100"))


# setup stuff ####################

app = Flask(__name__)
images: Dict[str, Image.Image] = {}
char_ids: List[str] = []

for path in pathlib.Path(IMAGE_PATH).iterdir():
    if not path.is_file():
        continue
    name = path.stem  # remove the extension
    images[name] = Image.open(path)
    char_ids.append(name)
    if app.env == "production":
        images[name].load()


# image processing functions #####

def _clamp(x, start, end):
    # note, if end < start, returns start
    return max(min(x, end), start)

def _center_and_nudge(
    crop_x: int,
    crop_y: int,
    crop_size: int,
    base_width: int,
    base_height: int,
) -> Tuple[int, int, int, int]:
    # create a square rect of width `crop_size` centered
    # around `(crop_x, crop_y)`, ensuring that it stays within
    # the rect `(0, 0, base_width, base_height)`
    half_size = crop_size//2

    x = _clamp(crop_x-half_size, 0, base_width-crop_size)
    y = _clamp(crop_y-half_size, 0, base_height-crop_size)
    w = min(crop_size, base_width)
    h = min(crop_size, base_height)
    return (x, y, x+w, y+h)


def _get_opaque_percentage(im: Image.Image) -> float:
    return (
        # count the number of fully opaque pixels
        im.getchannel("A").histogram()[255]
        # divide by total number of pixels
        / (im.width*im.height)
    )


def _get_byte_stream(im: Image.Image, mode: str) -> Tuple[io.BytesIO, str]:
    render_settings = FILE_FORMATS[mode]

    img_buf = io.BytesIO(b"")
    dim = max(im.width, im.height)

    for setting in render_settings:
        size = setting["maxsize"]
        if size == -1 or dim < size:
            reduce = setting["reduce"]
            if reduce > 1:
                im = im.reduce(reduce)
            im.save(img_buf, setting["format"], **setting["args"])
            format_used = setting["format"]
            break
    else:
        # else of for loop is executed when loop
        # ends without hitting a break, i.e. no
        # appropriate setting was found
        print("no appropriate setting was found (didn't end format list with maxsize: -1?)")
        # default to this so at least *some* image
        # comes out, even if it's not intended
        im.save(img_buf, "webp", lossless=False, quality=70, method=0)
        format_used = "webp"

    img_buf.flush()
    img_buf.seek(0)
    return (img_buf, format_used)


# fun decorators #################

def add_img_from_id(route_handler):
    @functools.wraps(route_handler)
    def wrapper(*args, **kwargs):
        # flask puts the variable route in kwargs
        im = images.get(kwargs["char_id"])
        if im is None:
            abort(404)

        kwargs["im"] = im

        return route_handler(*args, **kwargs)
    return wrapper


def convert_args(**arguments):
    def decorator(route_handler):
        @functools.wraps(route_handler)
        def wrapper(*args, **kwargs):
            for arg, converter in arguments.items():
                if type(converter) == tuple:
                    converter, default = converter
                else:
                    default = None

                try:
                    # pass the converted arguments into the
                    # wrapped function by adding them to kwargs
                    kwargs[arg] = converter(request.args[arg])
                except KeyError:
                    # if the argument is not in the request but
                    # was mandatory, 422. otherwise, use default
                    if default is None:
                        abort(422)
                    kwargs[arg] = default
                except ValueError:
                    # if the argument was invalid, abort even
                    # if it was optional
                    abort(422)

            return route_handler(*args, **kwargs)
        return wrapper
    return decorator


# flask stuff ####################

def generate(im: Image.Image, x: int, y: int, size: int, mode: str):
    cropped = im.crop(_center_and_nudge(x, y, size, im.width, im.height))
    return _get_byte_stream(cropped, mode)


def generate_new(im: Image.Image, size: int, threshold: float, mode: str):
    num_attempts = 0
    x_padding = PADDING

    while True:
        x = random.randint(x_padding, im.width-1-x_padding)
        y = random.randint(PADDING, im.height-1-PADDING)

        cropped = im.crop(_center_and_nudge(x, y, size, im.width, im.height))
        percentage = _get_opaque_percentage(cropped)
        if percentage >= threshold:
            break

        num_attempts += 1
        if num_attempts > 150:
            # after 150 failed attempts we can be pretty
            # sure the query is impossible to serve, but
            # theoretically it might still be possible.
            # maybe code 500 should be used instead
            # because it is possible the request would
            # succeed if sent again, unmodified, but the
            # chance is so low the arguments should
            # probably be adjusted
            abort(422)
        elif num_attempts > 5:
            x_padding = min(x_padding + PADDING//2, int(im.width*0.4))

    return (x, y, *_get_byte_stream(cropped, mode))


def get_size(step: int, difficulty: int) -> int:
    # todo: use difficulty
    return (9*step + 34)*step + 69


def get_random_char_id(charset: int) -> str:
    # todo: use charset
    return random.choice(char_ids)


def get_link(
    char_id: str, x: int, y: int,
    step: int, difficulty: int,
    mode: Optional[str]=None,
) -> str:
    args_dict = {"x": x, "y": y, "step": step, "difficulty": difficulty}
    if mode is not None:
        args_dict["mode"] = mode
    return f"/{char_id}?{urllib.parse.urlencode(args_dict)}"


def make_link_header(
    char_id: str, x: int, y: int,
    step: int, difficulty: int,
    mode: Optional[str]=None,
) -> str:
    return f'<{get_link(char_id, x, y, step, difficulty, mode)}>; rel="next"'


@app.route("/new", methods=["GET"])
@convert_args(
    difficulty=(int, 0),
    charset=(int, 0),
    mode=(str, DEFAULT_FORMAT),
)
def get_random_new(difficulty: int, charset: int, mode: str):
    if mode not in FILE_FORMATS:
        abort(422)

    # if threshold < 0 or threshold > 0.9:
    #     abort(422)
    # # should prevent most infinite loops...
    # if threshold*size > MAX_SIZE_THRESHOLD:
    #     abort(422)

    char_id = get_random_char_id(charset)
    x, y, stream, format = generate_new(
        images[char_id], get_size(0, difficulty), DEFAULT_THRESHOLD, mode,
    )

    return redirect(
        get_link(char_id, x, y, 0, difficulty, mode),
        code=303,
    )


@app.route("/<char_id>", methods=["GET"])
@add_img_from_id
@convert_args(
    x=int, y=int, step=int, difficulty=int,
    mode=(str, DEFAULT_FORMAT),
)
def generate_handler(
    char_id: str, im: Image.Image, x: int, y: int,
    step: int, difficulty: int, mode: str,
):
    if mode not in FILE_FORMATS:
        abort(422)
    size = get_size(step, difficulty)
    if size < 1:
        abort(422)

    stream, format = generate(im, x, y, size, mode)
    res = make_response(stream.getvalue())
    res.headers["Content-Type"] = f"image/{format}"

    if step < 9:  # todo: use difficulty
        res.headers["Link"] = make_link_header(char_id, x, y, step+1, difficulty, mode)
    return res
    # return send_file(stream, mimetype=f"image/{format}")
    # return _get_bytes(cropped, mode)
