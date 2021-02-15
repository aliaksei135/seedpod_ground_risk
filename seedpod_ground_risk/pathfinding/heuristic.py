import abc

import numpy as np

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
        def calc(grid, ny, nx, gy, gx, k, res):
            dist = ((nx - gx) ** 2 + (ny - gy) ** 2) ** 0.5
            n = int(dist) + 1
            line_x = np.linspace(nx, gx, n).astype(np.int)
            line_y = np.linspace(ny, gy, n).astype(np.int)
            line = np.unique(np.vstack((line_y, line_x)).T, axis=0)
            integral_val = grid[line[:, 0], line[:, 1]].sum()

            # return integral_val
            return ((k / dist) * integral_val) + dist
            # return k * integral_val + dist

        return calc(self.environment.grid, node.y, node.x, goal.y, goal.x, self.k, self.resolution)

        return ((self.k / dist) * integral_val) + dist
