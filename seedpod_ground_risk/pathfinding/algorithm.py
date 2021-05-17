import abc

from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node


class Algorithm(abc.ABC):

    @abc.abstractmethod
    def find_path(self, environment: GridEnvironment, start: Node, goal: Node):
        pass
