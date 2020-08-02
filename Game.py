import random
from typing import BinaryIO, List, Optional, Tuple, Dict

from TaggedImage import TaggedImage
import image_setup
import image_generator

characters: List[TaggedImage] = image_setup.images


class Game(object):
    def __init__(
        self,
        channel: int,
        num_rounds: int = 5,
        starting_radius: int = 30,
        help_radius: int = 5,
    ):
        self.channel: int = channel
        self.num_rounds: int = num_rounds
        self.starting_radius: int = starting_radius
        self.help_radius: int = help_radius

        self.current_image: Optional[TaggedImage] = None
        self.round = 0
        self.current_radius: int = starting_radius
        self.current_position: Tuple[int, int] = (0, 0)

        self.scores: Dict[int, int] = {}

    def start_round(self) -> BinaryIO:
        self.current_image = random.choice(characters)
        self.round += 1
        self.current_radius = self.starting_radius

        im = self.current_image.image

        buf = None
        while buf is None:
            self.current_position = (
                random.randint(self.starting_radius, im.width - self.starting_radius),
                random.randint(self.starting_radius, im.height - self.starting_radius),
            )
            buf = image_generator.generate_if_opaque(
                im,
                self.starting_radius,
                *self.current_position,
            )

        return buf

    def get_help(self) -> BinaryIO:
        if self.current_image is None:
            raise RuntimeError("current image was none while getting help")

        self.current_radius += self.help_radius

        return image_generator.generate(
            self.current_image.image,
            self.current_radius,
            *self.current_position,
        )

    def verify_answer(self, answer: str) -> bool:
        if self.current_image is None:
            raise RuntimeError("current image was none while verifying")

        return self.current_image.name.lower() in answer.lower()

    def end_round(self, winner: int) -> Optional[BinaryIO]:
        score = self.scores.get(winner)
        if score is None:
            self.scores[winner] = 1
        else:
            self.scores[winner] = score+1

        if self.round == self.num_rounds:
            return None
        else:
            return self.start_round()
