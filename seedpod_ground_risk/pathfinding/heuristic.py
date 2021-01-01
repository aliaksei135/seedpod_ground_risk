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
    from seedpod_ground_risk.pathfinding.environment import Environment

    def __init__(self, environment: Environment):
        from seedpod_ground_risk.pathfinding.a_star import AStar

        self.environment = environment
        self.pathfinder = AStar()

    def h(self, node: Node, goal: Node):
        path_to_goal = self.pathfinder.find_path(self.environment, node, goal)
        cumulative_val = 0
        for node in path_to_goal:
            cumulative_val += node.n
        return cumulative_val
