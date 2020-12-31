import abc

from seedpod_ground_risk.pathfinding.environment import Node


class Heuristic(abc.ABC):
    @abc.abstractmethod
    def h(self, node: Node, goal: Node):
        pass


class EuclideanHeuristic(Heuristic):
    def h(self, node: Node, goal: Node):
        pass


class ManhattanHeuristic(Heuristic):
    def h(self, node: Node, goal: Node):
        pass


class EuclideanRiskHeuristic(Heuristic):
    def h(self, node: Node, goal: Node):
        pass
