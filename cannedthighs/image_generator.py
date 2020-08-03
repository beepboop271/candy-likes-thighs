import io
from typing import BinaryIO, Optional, Tuple

from PIL import Image


def center_and_nudge(
    crop_x: int,
    crop_y: int,
    crop_size: int,
    base_width: int,
    base_height: int,
) -> Tuple[int, int, int, int]:
    half_size = int(crop_size/2)  # guaranteed to be whole
    rect_lx = crop_x-half_size
    rect_ly = crop_y-half_size
    rect_ux = crop_x+half_size
    rect_uy = crop_y+half_size

    if crop_size >= base_width:
        rect_lx = 0
        rect_ux = base_width-1
    elif rect_lx < 0:
        rect_ux += abs(rect_lx)
        rect_lx = 0
    elif rect_ux >= base_width:
        rect_lx -= rect_ux-base_width+1
        rect_ux = base_width-1

    if crop_size >= base_height:
        rect_ly = 0
        rect_uy = base_height-1
    elif rect_ly < 0:
        rect_uy += abs(rect_ly)
        rect_ly = 0
    elif rect_uy >= base_height:
        rect_ly -= rect_uy-base_height+1
        rect_uy = base_height-1

    return (
        rect_lx, rect_ly,
        rect_ux, rect_uy,
    )


def get_opaque_percentage(im: Image.Image) -> float:
    num_opaque: int = 0
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if len(p) > 3 and p[3] == 255:
                num_opaque += 1
    return num_opaque / (im.width*im.height)


def generate(
    base: Image.Image,
    size: int,
    x: int, y: int,
) -> BinaryIO:
    cropped = base.crop(center_and_nudge(x, y, size, base.width, base.height))

    buf = io.BytesIO(b"")
    cropped.save(buf, "PNG")

    return buf


def generate_if_opaque(
    base: Image.Image,
    size: int,
    x: int, y: int,
) -> Optional[BinaryIO]:
    cropped = base.crop(center_and_nudge(x, y, size, base.width, base.height))

    if get_opaque_percentage(cropped) < 0.5:
        return None

    buf = io.BytesIO(b"")
    cropped.save(buf, "PNG")

    return buf
