from PIL import Image


class TaggedImage(object):
    __slots__ = ("_image", "_name")

    def __init__(self, image: Image.Image, name: str):
        self._image = image
        self._name = name

    @property
    def image(self) -> Image.Image:
        return self._image

    @property
    def name(self) -> str:
        return self._name
