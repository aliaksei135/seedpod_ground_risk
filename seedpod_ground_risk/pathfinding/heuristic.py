import abc
from typing import Tuple

import numpy as np

from seedpod_ground_risk.pathfinding import bresenham


class Heuristic(abc.ABC):
    @abc.abstractmethod
    def h(self, node: Tuple[int, int], goal: Tuple[int, int]):
        pass


class RiskHeuristic(Heuristic, abc.ABC):
    from seedpod_ground_risk.pathfinding.environment import Environment

    def __init__(self, environment: Environment, risk_to_dist_ratio=1, resolution=1):
        self.environment = environment
        self.resolution = resolution
        self.max = environment.grid.max()
        self.k = risk_to_dist_ratio


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

        # @jit(nopython=True)
        def calc(grid, ny, nx, gy, gx, k):
            dist = ((nx - gx) ** 2 + (ny - gy) ** 2) ** 0.5
            line = bresenham.make_line(nx, ny, gx, gy)
            integral_val = grid[line[:, 0], line[:, 1]].sum()
            # integral_val = 0
            # for y, x in line:
            #     integral_val += grid[y, x]
            # integral_val = np.array([grid[y, x] for y, x in line]).sum()

            if integral_val > 1:
                r = k * np.log10(integral_val)
                if r > 0:
                    return r + dist
            return dist

        return calc(self.environment.grid, node[0], node[1], goal[0], goal[1], self.k)


class ManhattanRiskHeuristic(RiskHeuristic):
    def h(self, node: Tuple[int, int], goal: Tuple[int, int]):
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

            if integral_val > 1:
                r = k * np.log10(integral_val)
                if r > 0:
                    return r + dist
            return dist

        return calc(self.environment.grid, node[0], node[1], goal[0], goal[1], self.k)
