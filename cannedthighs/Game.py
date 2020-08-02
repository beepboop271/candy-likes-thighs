import random
from typing import BinaryIO, Dict, List, Optional, Tuple

from cannedthighs import image_generator
from cannedthighs import image_setup
from cannedthighs.TaggedImage import TaggedImage

characters: List[TaggedImage] = image_setup.images


class Game(object):
    __slots__ = (
        "_num_rounds",
        "_starting_radius",
        "_help_radius",
        "_current_image",
        "_current_round",
        "_current_radius",
        "_current_position",
        "_scores",
    )    

    def __init__(
        self,
        num_rounds: int = 5,
        starting_radius: int = 30,
        help_radius: int = 30,
    ):
        self._num_rounds: int = num_rounds
        self._starting_radius: int = starting_radius
        self._help_radius: int = help_radius

        self._current_image: Optional[TaggedImage] = None
        self._current_round: int = 0
        self._current_radius: int = starting_radius
        self._current_position: Tuple[int, int] = (0, 0)

        self._scores: Dict[int, int] = {}

    def start_round(self) -> BinaryIO:
        self._current_image = random.choice(characters)
        self._current_round += 1

        return self.reset_round()

    def reset_round(self) -> BinaryIO:
        if self._current_image is None:
            raise RuntimeError("current image was none while resetting")

        self._current_radius = self._starting_radius

        im = self._current_image.image

        buf = None
        while buf is None:
            self._current_position = (
                random.randint(self._starting_radius, im.width - self._starting_radius),
                random.randint(self._starting_radius, im.height - self._starting_radius),
            )
            buf = image_generator.generate_if_opaque(
                im,
                self._starting_radius,
                *self._current_position,
            )

        return buf

    def get_help(self) -> BinaryIO:
        if self._current_image is None:
            raise RuntimeError("current image was none while getting help")

        self._current_radius += self._help_radius

        return image_generator.generate(
            self._current_image.image,
            self._current_radius,
            *self._current_position,
        )

    def verify_answer(self, answer: str) -> bool:
        if self._current_image is None:
            raise RuntimeError("current image was none while verifying")

        return self._current_image.name.lower() in answer.lower()

    def end_round(self, winner: int) -> Optional[BinaryIO]:
        score = self._scores.get(winner)
        if score is None:
            self._scores[winner] = 1
        else:
            self._scores[winner] = score+1

        if self._current_round == self._num_rounds:
            return None
        else:
            return self.start_round()

    @property
    def current_radius(self) -> int:
        return self._current_radius

    @property
    def current_round(self) -> int:
        return self._current_round

    @property
    def scores(self) -> Tuple[Tuple[int, int], ...]:
        return tuple(self._scores.items())
