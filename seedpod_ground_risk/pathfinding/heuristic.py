import abc
from typing import Tuple

import numpy as np

from seedpod_ground_risk.pathfinding import bresenham


class Heuristic(abc.ABC):
    @abc.abstractmethod
    def h(self, node: Tuple[int, int], goal: Tuple[int, int]):
        pass


class RiskHeuristic(Heuristic, abc.ABC):
    from seedpod_ground_risk.pathfinding.environment import GridEnvironment

    def __init__(self, environment: GridEnvironment, risk_to_dist_ratio=1, resolution=1):
        self.environment = environment
        self.resolution = resolution
        self.max = environment.grid.max()
        self.k = risk_to_dist_ratio if risk_to_dist_ratio > 0 else 0


class EuclideanHeuristic(Heuristic):
    def h(self, node: Tuple[int, int], goal: Tuple[int, int]):
        return ((node[0] - goal[0]) ** 2 + (node[1] - goal[1]) ** 2) ** 0.5


class ManhattanHeuristic(Heuristic):
    def h(self, node: Tuple[int, int], goal: Tuple[int, int]):
        return abs((node[0] - goal[0])) + abs((node[1] - goal[1]))


class EuclideanRiskHeuristic(RiskHeuristic):
    def h(self, node: Tuple[int, int], goal: Tuple[int, int]):
        if node == goal:
            return 0

        dist = ((node[1] - goal[1]) ** 2 + (node[0] - goal[0]) ** 2) ** 0.5
        line = bresenham.make_line(node[1], node[0], goal[1], goal[0])
        integral_val = self.environment.grid[line[:, 0], line[:, 1]].sum()

        if integral_val > 1:
            return self.k * np.log10(integral_val) + dist
        else:
            return dist


class ManhattanRiskHeuristic(RiskHeuristic):
    def h(self, node: Tuple[int, int], goal: Tuple[int, int]):
        if node == goal:
            return 0

        dist = abs((node[1] - goal[1])) + abs((node[0] - goal[0]))
        line = bresenham.make_line(node[1], node[0], goal[1], goal[0])
        integral_val = self.environment.grid[line[:, 0], line[:, 1]].sum()

        if integral_val > 1:
            return self.k * np.log10(integral_val) + dist
        else:
            return dist
