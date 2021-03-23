import abc
from typing import Tuple

from seedpod_ground_risk.pathfinding.environment import GridEnvironment


class Algorithm(abc.ABC):

    @abc.abstractmethod
    def find_path(self, environment: GridEnvironment, start: Tuple[int, int], goal: Tuple[int, int]):
        pass
