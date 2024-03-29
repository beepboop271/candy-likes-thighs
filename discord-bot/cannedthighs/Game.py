import asyncio
import random
import time
from typing import Dict, Optional, TYPE_CHECKING, Tuple

import cannedthighs
from cannedthighs import image_generator
from cannedthighs.TaggedImage import TaggedImage

if TYPE_CHECKING:
    import discord


class Game(object):
    __slots__ = (
        "_NUM_ROUNDS",
        "_IMAGE_MODE",
        "_current_image",
        "_current_round",
        "_expansion_count",
        "_current_position",
        "_scores",
        "_render_lock",
    )

    def __init__(
        self,
        num_rounds: Optional[int] = None,
        *,
        image_mode: Optional[str] = None,
    ):
        if num_rounds is None:
            num_rounds = cannedthighs.conf.default_rounds
        if image_mode is None:
            image_mode = cannedthighs.conf.default_format

        self._NUM_ROUNDS: int = num_rounds
        self._IMAGE_MODE: str = image_mode

        self._current_image: Optional[TaggedImage] = None
        self._current_round: int = 0
        self._expansion_count: int = 0
        self._current_position: Tuple[int, int] = (0, 0)

        self._scores: Dict[int, int] = {}

        # to prevent spamming of image loading
        self._render_lock: asyncio.Lock = asyncio.Lock()

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

    def start_round(self) -> "discord.File":
        self._current_image = random.choice(cannedthighs.conf.images)
        self._current_round += 1

        return self.reset_round()

    def get_help(self) -> "discord.File":
        self._expansion_count += 1

        return self.view_image()

    def reset_round(self) -> "discord.File":
        if self._current_image is None:
            raise RuntimeError("current image was none while resetting")

        self._expansion_count = 0
        size = cannedthighs.conf.get_size(self._expansion_count)
        half_size = size//2

        im = self._current_image.image

        s = time.perf_counter_ns()
        n = 0
        img_buf = None
        while img_buf is None:
            self._current_position = (
                random.randint(half_size, im.width-half_size),
                random.randint(half_size, im.height-half_size),
            )
            img_buf = image_generator.generate_if_opaque(
                im,
                self._IMAGE_MODE,
                size,
                *self._current_position,
            )
            n += 1
        e = time.perf_counter_ns()
        print(f"new {size}: {n}, {(e-s)/1000000} ms, {img_buf.fp.getbuffer().nbytes/1000} KB")

        return img_buf

    def view_image(self) -> "discord.File":
        if self._current_image is None:
            raise RuntimeError("current image was none while getting image")

        size = cannedthighs.conf.get_size(self._expansion_count)

        s = time.perf_counter_ns()
        img_buf = image_generator.generate(
            self._current_image.image,
            self._IMAGE_MODE,
            size,
            *self._current_position,
        )
        e = time.perf_counter_ns()
        print(f"{size}: {(e-s)/1000000} ms, {img_buf.fp.getbuffer().nbytes/1000} KB")

        return img_buf

    def verify_answer(self, answer: str) -> bool:
        if self._current_image is None:
            return False

        return answer.lower() in self._current_image

    def end_round(self, winner: Optional[int]) -> Optional["discord.File"]:
        if winner is not None:
            self._scores[winner] = self._scores.get(winner, 0) + 1

        if self._current_round == self._NUM_ROUNDS:
            # end the game
            self._current_image = None
            return None

        return self.start_round()

    @property
    def current_round(self) -> int:
        return self._current_round

    @property
    def render_lock(self) -> asyncio.Lock:
        return self._render_lock
