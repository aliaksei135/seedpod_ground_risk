import abc

from seedpod_ground_risk.pathfinding.environment import Node


class Heuristic(abc.ABC):
    @abc.abstractmethod
    def h(self, node: Node, goal: Node):
        pass


class EuclideanHeuristic(Heuristic):
    def h(self, node: Node, goal: Node):
        return ((node.x - goal.x) ** 2 + (node.y - goal.y) ** 2) ** 0.5


class ManhattanHeuristic(Heuristic):
    def h(self, node: Node, goal: Node):
        return abs((node.x + node.y) - (goal.x + goal.y))


class EuclideanRiskHeuristic(Heuristic):
    def h(self, node: Node, goal: Node):
        pass
