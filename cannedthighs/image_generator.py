import io
from typing import Optional, Tuple

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
    half_size = int(crop_size/2)  # crop_size guaranteed to be even
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


def _get_buffer(im: Image.Image) -> io.BytesIO:
    # s = time.perf_counter_ns()
    img_buf = io.BytesIO(b"")
    if im.width < 400 and im.height < 400:
        im.save(img_buf, "webp", lossless=True, quality=50, method=0)
    elif im.width < 1000 and im.height < 1000:
        im.save(img_buf, "webp", lossless=False, quality=70, method=0)
    else:
        # half the size first
        im.reduce(2).save(img_buf, "webp", lossless=False, quality=70, method=0)
    # e = time.perf_counter_ns()
    # print(f"test: {(e-s)/1000000} ms, {img_buf.getbuffer().nbytes/1000} kb")

    # seek back to the start after writing to the
    # buffer, allowing a reader to read the buffer
    img_buf.seek(0)
    return img_buf


def generate(
    base: Image.Image,
    size: int,
    x: int, y: int,
) -> io.BytesIO:
    cropped = base.crop(_center_and_nudge(x, y, size, base.width, base.height))

    return _get_buffer(cropped)


def generate_if_opaque(
    base: Image.Image,
    size: int,
    x: int, y: int,
) -> Optional[io.BytesIO]:
    cropped = base.crop(_center_and_nudge(x, y, size, base.width, base.height))

    if _get_opaque_percentage(cropped) < cannedthighs.OPAQUE_THRESHOLD:
        return None

    return _get_buffer(cropped)
