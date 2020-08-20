import math
from typing import Any, Set

from PIL import Image


class TaggedImage(object):
    __slots__ = (
        "_image",
        "_names",
    )

    def __init__(self, image: Image.Image, *names: str):
        self._image = image
        self._names: Set[str] = set(names)

    def __contains__(self, other: Any) -> bool:
        if type(other) != str:
            return False

        return other in self._names

    def get_size_from_percentage(self, area_percentage: float) -> int:
        square_size = max(self._image.width, self._image.height)
        area = (area_percentage/100) * (square_size*square_size)
        ceil = math.ceil(math.sqrt(area))
        if (ceil & 1) == 1:
            return ceil-1
        return ceil

    @property
    def image(self) -> Image.Image:
        return self._image
