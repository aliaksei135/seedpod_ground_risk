import abc

import numpy as np

from seedpod_ground_risk.pathfinding import bresenham
from seedpod_ground_risk.pathfinding.environment import Node


class Heuristic(abc.ABC):
    @abc.abstractmethod
    def h(self, node: Node, goal: Node):
        pass


class RiskHeuristic(Heuristic, abc.ABC):
    from seedpod_ground_risk.pathfinding.environment import Environment

    def __init__(self, environment: Environment, risk_to_dist_ratio=1, resolution=1):
        self.environment = environment
        self.resolution = resolution
        self.max = environment.grid.max()
        self.k = risk_to_dist_ratio


class EuclideanHeuristic(Heuristic):
    def h(self, node: Node, goal: Node):
        return ((node.x - goal.x) ** 2 + (node.y - goal.y) ** 2) ** 0.5


class ManhattanHeuristic(Heuristic):
    def h(self, node: Node, goal: Node):
        return abs((node.x - goal.x)) + abs((node.y - goal.y))


class EuclideanRiskHeuristic(RiskHeuristic):
    def h(self, node: Node, goal: Node):
        if node == goal:
            return 0

        # @jit(nopython=True)
        def calc(grid, ny, nx, gy, gx, k):
            dist = ((nx - gx) ** 2 + (ny - gy) ** 2) ** 0.5
            line = bresenham.make_line(nx, ny, gx, gy)
            integral_val = grid[line[:, 0], line[:, 1]].sum()
            # integral_val = 0
            # for y, x in line:
            #     integral_val += grid[y, x]
            # integral_val = np.array([grid[y, x] for y, x in line]).sum()

            if integral_val > 0:
                return k * np.log10(integral_val) + dist
            else:
                return dist

        return calc(self.environment.grid, node.y, node.x, goal.y, goal.x, self.k)


class ManhattanRiskHeuristic(RiskHeuristic):
    def h(self, node: Node, goal: Node):
        if node == goal:
            return 0

        # @jit(nopython=True)
        def calc(grid, ny, nx, gy, gx, k):
            dist = abs((nx - gx)) + abs((ny - gy))
            line = bresenham.make_line(nx, ny, gx, gy)
            integral_val = grid[line[:, 0], line[:, 1]].sum()
            # integral_val = np.array([grid[y, x] for y, x in line]).sum()
            # integral_val = 0
            # for y, x in line:
            #     integral_val += grid[y, x]

            if integral_val > 0:
                return k * np.log10(integral_val) + dist
            else:
                return dist

        return calc(self.environment.grid, node.y, node.x, goal.y, goal.x, self.k)
