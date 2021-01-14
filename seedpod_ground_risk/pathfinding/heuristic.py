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

    def __init__(self, environment: Environment, risk_multiplier=1e9, resolution=1):
        from scipy.interpolate import RectBivariateSpline

        self.environment = environment
        self.resolution = resolution
        self.interpolater = RectBivariateSpline(range(400), range(400), environment.grid)
        self.k = risk_multiplier

    def h(self, node: Node, goal: Node):
        dist = ((node.x - goal.x) ** 2 + (node.y - goal.y) ** 2) ** 0.5
        line_2d = np.linspace(start=(node.x, node.y), stop=(goal.x, goal.y), num=int(dist / self.resolution),
                              endpoint=True)
        cs = np.cumsum(np.sqrt(np.sum(np.diff(line_2d, axis=0) ** 2, axis=1)))
        interp_2d = self.interpolater.ev(line_2d[:, 0], line_2d[:, 1])
        integral_val = np.trapz(interp_2d[:-1], cs)

        return self.k * integral_val
