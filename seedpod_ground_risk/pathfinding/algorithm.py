import abc

from seedpod_ground_risk.pathfinding.environment import Environment, Node


class Algorithm(abc.ABC):

    @abc.abstractmethod
    def find_path(self, environment: Environment, start: Node, goal: Node):
        pass
