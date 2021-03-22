import abc
from typing import Tuple

from seedpod_ground_risk.pathfinding.environment import Environment


class Algorithm(abc.ABC):

    @abc.abstractmethod
    def find_path(self, environment: Environment, start: Tuple[int, int], goal: Tuple[int, int]):
        pass
