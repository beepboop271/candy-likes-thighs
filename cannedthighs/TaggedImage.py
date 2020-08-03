import math

from PIL import Image


class TaggedImage(object):
    __slots__ = (
        "_image",
        "_name",
    )

    def __init__(self, image: Image.Image, name: str):
        self._image = image
        self._name = name

    def get_size_from_percentage(self, area_percentage: float) -> int:
        area = (area_percentage/100) * (self._image.width*self._image.height)
        ceil = math.ceil(math.sqrt(area))
        if (ceil & 1) == 1:
            return ceil-1
        return ceil

    @property
    def image(self) -> Image.Image:
        return self._image

    @property
    def name(self) -> str:
        return self._name
