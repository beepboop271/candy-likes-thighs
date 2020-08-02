import io
from typing import BinaryIO, Optional

from PIL import Image


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
    radius: int,
    x: int, y: int,
) -> BinaryIO:
    # out of bounds crop is acceptable, fills with zeroes
    cropped = base.crop((x-radius, y-radius, x+radius, y+radius))

    buf = io.BytesIO(b"")
    cropped.save(buf, "PNG")

    return buf


def generate_if_opaque(
    base: Image.Image,
    radius: int,
    x: int, y: int,
) -> Optional[BinaryIO]:
    cropped = base.crop((x-radius, y-radius, x+radius, y+radius))

    if get_opaque_percentage(cropped) < 0.5:
        return None

    buf = io.BytesIO(b"")
    cropped.save(buf, "PNG")

    return buf
