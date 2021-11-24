import numpy as np
from scipy.optimize import minimize_scalar

from seedpod_ground_risk.pathfinding import get_path_risk_sum
from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node
from seedpod_ground_risk.pathfinding.theta_star import RiskThetaStar


class IterativeRiskThetaStar(Algorithm):
    def find_path(self, environment: GridEnvironment, start: Node, goal: Node, target: float = 5e-6, niter=50,
                  atol=None, bracket=None):
        atol = atol if atol is not None else np.power(10, np.log10(target) - 2)
        bracket = bracket if bracket is not None else (
            np.power(10, np.log10(target) - 3), np.power(10, np.log10(target) + 3))
        algo = RiskThetaStar()
        grid = environment.grid

        def f(thres):
            path = algo.find_path(environment, start, goal, thres)
            if path is None:
                return np.inf
            return abs(get_path_risk_sum(path, grid) - target)

        res = minimize_scalar(f, method='brent', bracket=bracket, tol=atol, options=dict(maxiter=niter))
        print(f"Converged thres: {res.x}")

        return algo.find_path(environment, start, goal, res.x)
