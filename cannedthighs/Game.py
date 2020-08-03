import random
from typing import BinaryIO, Dict, List, Optional, Tuple

from cannedthighs import image_generator
from cannedthighs import image_setup
from cannedthighs.TaggedImage import TaggedImage

characters: List[TaggedImage] = image_setup.images


class Game(object):
    __slots__ = (
        "_num_rounds",
        "_starting_percentage",
        "_help_coeff",
        "_current_image",
        "_current_round",
        "_expansion_count",
        "_current_position",
        "_scores",
    )

    def __init__(
        self,
        num_rounds: int = 5,
        starting_percentage: float = 0.15,
        help_coeff: float = 0.3,
    ):
        self._num_rounds: int = num_rounds
        self._starting_percentage: float = starting_percentage
        self._help_coeff: float = help_coeff

        self._current_image: Optional[TaggedImage] = None
        self._current_round: int = 0
        self._expansion_count: float = 0
        self._current_position: Tuple[int, int] = (0, 0)

        self._scores: Dict[int, int] = {}

    def start_round(self) -> BinaryIO:
        self._current_image = random.choice(characters)
        self._current_round += 1

        return self.reset_round()

    def reset_round(self) -> BinaryIO:
        if self._current_image is None:
            raise RuntimeError("current image was none while resetting")

        self._expansion_count = 0
        size = self._current_image.get_size_from_percentage(self.current_percentage)

        im = self._current_image.image

        buf = None
        while buf is None:
            self._current_position = (
                random.randint(0, im.width),
                random.randint(0, im.height),
            )
            buf = image_generator.generate_if_opaque(
                im,
                size,
                *self._current_position,
            )

        return buf

    def get_help(self) -> BinaryIO:
        if self._current_image is None:
            raise RuntimeError("current image was none while getting help")

        self._expansion_count += 1
        size = self._current_image.get_size_from_percentage(self.current_percentage)

        return image_generator.generate(
            self._current_image.image,
            size,
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
    def current_percentage(self) -> float:
        return min(
            100,

            self._help_coeff
            * (2**self._expansion_count + self._expansion_count**2)
            + self._starting_percentage,
        )

    @property
    def current_round(self) -> int:
        return self._current_round

    @property
    def scores(self) -> Tuple[Tuple[int, int], ...]:
        return tuple(self._scores.items())
