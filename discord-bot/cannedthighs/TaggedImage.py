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

    @property
    def image(self) -> Image.Image:
        return self._image
