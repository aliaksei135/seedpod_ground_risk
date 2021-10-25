import abc

from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node


class Algorithm(abc.ABC):

    def __init__(self, **kwargs) -> None:
        super().__init__()

    @abc.abstractmethod
    def find_path(self, environment: GridEnvironment, start: Node, goal: Node, **kwargs):
        pass
