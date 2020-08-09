import asyncio
import cannedthighs
import random
from typing import BinaryIO, Dict, Optional, Tuple

from cannedthighs import image_generator
from cannedthighs import image_setup
from cannedthighs.TaggedImage import TaggedImage


class Game(object):
    __slots__ = (
        "_NUM_ROUNDS",
        "_PERCENTAGE_SHIFT",
        "_EXPANSION_COEFF",
        "_current_image",
        "_current_round",
        "_expansion_count",
        "_reset_count",
        "_current_position",
        "_scores",
        "_expand_lock",
    )

    def __init__(
        self,
        num_rounds: int = cannedthighs.DEFAULT_ROUNDS,
        percentage_shift: float = cannedthighs.DEFAULT_SHIFT,
        help_coeff: float = cannedthighs.DEFAULT_COEFF,
    ):
        self._NUM_ROUNDS: int = num_rounds
        self._PERCENTAGE_SHIFT: float = percentage_shift
        self._EXPANSION_COEFF: float = help_coeff

        self._current_image: Optional[TaggedImage] = None
        self._current_round: int = 0
        self._expansion_count: int = 0
        self._reset_count: int = 0
        self._current_position: Tuple[int, int] = (0, 0)

        self._scores: Dict[int, int] = {}

        self._expand_lock: asyncio.Lock = asyncio.Lock()

    def __str__(self) -> str:
        # game.scores: ((player_id_1, score_1), (player_id_2, score_2), ...)
        # sort from highest score to lowest
        # enumerate with first place, second place, ...
        # ((1, (player_id_1, score_1)), (2, (player_id_2, score_2)), ...)
        scores = enumerate(
            sorted(
                self._scores.items(),
                key=lambda x: x[1],
                reverse=True
            ),
            1,
        )
        score_str = "\n".join([
            f"#{place} <@{player}>: {score} points"
            for place, (player, score) in scores
        ])
        return f"Round {self._current_round}/{self._NUM_ROUNDS}\n{score_str}"

    def start_round(self) -> BinaryIO:
        self._current_image = random.choice(image_setup.images)
        self._current_round += 1

        return self.reset_round()

    def get_help(self) -> BinaryIO:
        self._expansion_count += 1

        return self.view_image()

    def reset_round(self) -> BinaryIO:
        if self._current_image is None:
            raise RuntimeError("current image was none while resetting")

        self._expansion_count = 0
        self._reset_count += 1
        size = self._current_image.get_size_from_percentage(self.current_percentage)
        half_size = size//2

        im = self._current_image.image

        img_buf = None
        while img_buf is None:
            self._current_position = (
                random.randint(half_size, im.width-half_size),
                random.randint(half_size, im.height-half_size),
            )
            img_buf = image_generator.generate_if_opaque(
                im,
                size,
                *self._current_position,
            )

        return img_buf

    def view_image(self) -> BinaryIO:
        if self._current_image is None:
            raise RuntimeError("current image was none while getting image")

        size = self._current_image.get_size_from_percentage(self.current_percentage)

        img_buf = image_generator.generate(
            self._current_image.image,
            size,
            *self._current_position,
        )

        return img_buf

    def verify_answer(self, answer: str) -> bool:
        if self._current_image is None:
            return False

        return answer.lower() in self._current_image

    def end_round(self, winner: int) -> Optional[BinaryIO]:
        self._scores[winner] = self._scores.get(winner, 0) + 1

        if self._current_round == self._NUM_ROUNDS:
            # end the game
            self._current_image = None
            return None

        return self.start_round()

    @property
    def current_percentage(self) -> float:
        return min(
            100,

            self._EXPANSION_COEFF
            * (2**self._expansion_count + self._expansion_count**2)
            + self._PERCENTAGE_SHIFT,
        )

    @property
    def current_round(self) -> int:
        return self._current_round

    @property
    def expand_lock(self) -> asyncio.Lock:
        return self._expand_lock
