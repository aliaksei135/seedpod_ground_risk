import abc

import numpy as np

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
        return abs((node.x - goal.x)) + abs((node.y - goal.y))


class EuclideanRiskHeuristic(Heuristic):
    from seedpod_ground_risk.pathfinding.environment import Environment

    def __init__(self, environment: Environment, risk_multiplier=1e-6, distance_multiplier=1, resolution=1):
        self.environment = environment
        self.resolution = resolution
        self.kr = risk_multiplier
        self.kd = distance_multiplier

    def h(self, node: Node, goal: Node):
        dist = ((node.x - goal.x) ** 2 + (node.y - goal.y) ** 2) ** 0.5
        n = int(dist / self.resolution)
        line_2d = np.linspace(start=(node.x, node.y), stop=(goal.x, goal.y), num=n,
                              endpoint=True)
        grid_coords = np.array(np.round(line_2d), dtype=np.intp)
        grid_vals = self.environment.grid[grid_coords[:, 0], grid_coords[:, 1]]
        integral_val = np.trapz(grid_vals)

        return self.kr * integral_val  # + self.kd * dist