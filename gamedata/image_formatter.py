# reads files from https://github.com/Aceship/AN-EN-Tags
# resizes all 2048x2048 images to 1024x1024, so all
# images are uniform size, then trims each image to
# the bounding box of the opaque contents, plus
# padding (i.e. gets rid of excess transparent pixels)

# exmple usage:
# $ python image_formatter.py "../AN-EN-Tags" "./images"
#          ^                  ^               ^
# name of script              |               |
# path to the base folder of AN-EN-Tags       |
# path to the folder inside which files should be saved

import glob
import json
import os
import sys
import time
from typing import FrozenSet, List, Tuple

from PIL import Image, ImageEnhance


# amount of transparent padding to add
PADDING = 40
# file format of output
FORMAT = "png"

# source: path to the base folder of AN-EN-Tags
# dest: path to the folder inside which files should be saved
SOURCE, DEST = sys.argv[1:]

# don't process/output files specified here
with open("image_setup.json", encoding="utf-8") as setup_data:
    EXCLUDE: FrozenSet[str] = frozenset(json.load(setup_data)["excludeList"])

images: List[Tuple[Image.Image, str]] = []


# directions:
# 0: top side (y = 0)
# 1: right side (x = width-1)
# 2: bottom side (y = height-1)
# 3: left side (x = 0)

def check_dir(
    im: Image.Image,
    inner: int, outer: int,
    low: int, high: int,
    direction: int,
) -> int:
    # binary search to find the boundary of opaque
    # content in the image:
    #
    # example:
    # find left boundary after already finding top boundary:
    # ┌───────┬───────┐<-top of original image
    # ├───────┼───────┤<-low (top of image that isn't transparent)
    # │       │       │
    # │       │       │
    # │       │       │
    # │       │       │
    # └───────┴───────┘<-high
    # ^outer  ^inner
    #
    # crop the outer half from low to high to check
    # (ignore the top part we already know is transparent)
    # ┌───────┬───────┐
    # ├───┬───┼───────┤
    # │xxx│   │       │
    # │xxx│   │       │
    # │xxx│   │       │
    # │xxx│   │       │
    # └───┴───┴───────┘
    # ^outer  ^inner
    #
    # if the outer half is completely blank, we know the
    # boundary must be somewhere in the inner half.
    # if the outer half is not completely blank, we know
    # the boundary must be somewhere in the outer half.
    #
    # case: the boundary is in the inner half
    # ┌───────┬───────┐
    # ├───┬───┼───────┤
    # │   │   │       │
    # │   │   │       │
    # │   │   │       │
    # │   │   │       │
    # └───┴───┴───────┘
    #     ^   ^inner
    #     outer
    #
    # crop the outer half to check
    # ┌───────┬───────┐
    # ├───┬─┬─┼───────┤
    # │   │x│ │       │
    # │   │x│ │       │
    # │   │x│ │       │
    # │   │x│ │       │
    # └───┴─┴─┴───────┘
    #     ^   ^inner
    #     outer
    #
    # if the outer half is completely blank, we know the
    # boundary must be somewhere in the inner half.
    # if the outer half is not completely blank, we know
    # the boundary must be somewhere in the outer half.
    #
    # repeat recursion until the inner and outer border
    # converge

    if abs(outer-inner) <= 1:
        return outer

    half = inner + (outer-inner)//2

    if direction == 0:
        rect = (low, outer, high, half)
    elif direction == 1:
        rect = (half, low, outer, high)
    elif direction == 2:
        rect = (low, half, high, outer)
    else:
        rect = (outer, low, half, high)
    crop = im.crop(rect)

    if crop.histogram()[0] / (crop.width*crop.height) > 0.999:
        # consider >99.9% empty as empty
        return check_dir(im, inner, half, low, high, direction)

    return check_dir(im, half, outer, low, high, direction)


def get_bounds(im: Image.Image) -> Tuple[int, int, int, int]:
    left = check_dir(im,   im.width//2,  0,         0,    im.height, 3)
    # use the information from previous boundaries to save a bit of time
    top = check_dir(im,    im.height//2, 0,         left, im.width,  0)
    right = check_dir(im,  im.width//2,  im.width,  top,  im.height, 1)
    bottom = check_dir(im, im.height//2, im.height, left, right,     2)
    return (left-PADDING, top-PADDING, right+PADDING, bottom+PADDING)


def crop(im: Image.Image) -> Image.Image:
    return im.crop(get_bounds(
        # the R, G, and B channels don't help us find
        # the bounds, discard them to save a lot of time.
        # some of the 2048x2048 images have a dumb border
        # 1 pixel wide with an alpha value of 1, so
        # increase the contrast by a decent amount to get
        # rid of the border
        ImageEnhance.Contrast(im.getchannel("A")).enhance(5.0),
    ))


def save(images: List[Tuple[Image.Image, str]]):
    for im, name in images:
        # example name: char_002_amiya_1.png
        # first 5 characters are always "char_", so,
        # search for the next "_" to cut off the char
        # number. also remove "#" character (found in
        # skin names)
        name = name[name.index("_", 5) + 1:].replace("#", "")

        # remove "+" character (only used for amiya's e1 art)
        if name == "amiya_1+.png":
            name = "amiya_1_2.png"

        im.save(f"{DEST}/{name}", FORMAT)


for file in glob.glob(f"{SOURCE}/img/characters/*"):
    filename = os.path.basename(file)
    if filename not in EXCLUDE:
        im: Image.Image = Image.open(file)
        im.load()
        print(filename, end=" ")

        s = time.perf_counter_ns()

        if im.width > 1024 or im.height > 1024:
            im = im.reduce(2)

        images.append((crop(im), filename))

        e = time.perf_counter_ns()
        print(f"{(e-s)/1000000}ms")

# make sure the user doesn't accidentally bomb a
# random folder with hundreds of images
if input(
    f"save {len(images)} images to '{os.path.realpath(DEST)}/*.{FORMAT}'? (y/n) "
).lower() == "y":
    save(images)
