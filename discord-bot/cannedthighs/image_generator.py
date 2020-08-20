import io
from typing import Optional, Tuple

import discord
from PIL import Image

import cannedthighs


def _center_and_nudge(
    crop_x: int,
    crop_y: int,
    crop_size: int,
    base_width: int,
    base_height: int,
) -> Tuple[int, int, int, int]:
    # create a rect of width `crop_size` centered around
    # `(crop_x, crop_y)`, ensuring that it stays within
    # the rect `(0, 0, base_width, base_height)`
    half_size = crop_size//2  # note: crop_size guaranteed to be even
    rect_lx = crop_x-half_size
    rect_ly = crop_y-half_size
    rect_ux = crop_x+half_size
    rect_uy = crop_y+half_size

    if crop_size >= base_width:
        rect_lx = 0
        rect_ux = base_width
    elif rect_lx < 0:
        rect_ux += abs(rect_lx)
        rect_lx = 0
    elif rect_ux > base_width:
        rect_lx -= rect_ux-base_width
        rect_ux = base_width

    if crop_size >= base_height:
        rect_ly = 0
        rect_uy = base_height
    elif rect_ly < 0:
        rect_uy += abs(rect_ly)
        rect_ly = 0
    elif rect_uy > base_height:
        rect_ly -= rect_uy-base_height
        rect_uy = base_height

    return (
        rect_lx, rect_ly,
        rect_ux, rect_uy,
    )


def _get_opaque_percentage(im: Image.Image) -> float:
    return (
        # count the number of fully opaque pixels
        im.getchannel("A").histogram()[255]
        # divide by total number of pixels
        / (im.width*im.height)
    )


def _get_file(im: Image.Image, mode: str) -> discord.File:
    render_settings = cannedthighs.FILE_FORMATS[mode]

    img_buf = io.BytesIO(b"")
    dim = max(im.width, im.height)

    for setting in render_settings:
        size = setting["maxsize"]
        if size == -1 or dim < size:
            reduce = setting["reduce"]
            if reduce > 1:
                im = im.reduce(reduce)
            img_format = setting["format"]
            im.save(img_buf, img_format, **setting["args"])
            break
    else:
        # else of for loop is executed when loop
        # ends without hitting a break, i.e. no
        # appropriate setting was found
        print("no appropriate setting was found (didn't end format list with maxsize: -1?)")
        # default to this so at least *some* image
        # comes out, even if it's not intended
        img_format = "webp"
        im.save(img_buf, img_format, lossless=False, quality=70, method=0)

    # seek back to the start after writing to the
    # buffer, allowing a reader to read the buffer
    img_buf.seek(0)
    return discord.File(img_buf, f"{cannedthighs.FILE_NAME}.{img_format}")


def generate(
    base: Image.Image,
    mode: str,
    size: int,
    x: int, y: int,
) -> discord.File:
    cropped = base.crop(_center_and_nudge(x, y, size, base.width, base.height))

    return _get_file(cropped, mode)


def generate_if_opaque(
    base: Image.Image,
    mode: str,
    size: int,
    x: int, y: int,
) -> Optional[discord.File]:
    cropped = base.crop(_center_and_nudge(x, y, size, base.width, base.height))

    if _get_opaque_percentage(cropped) < cannedthighs.OPAQUE_THRESHOLD:
        return None

    return _get_file(cropped, mode)
