import numpy as np

cimport numpy as np
from scipy.optimize import minimize_scalar

np.import_array()
from seedpod_ground_risk.pathfinding import get_path_risk_sum
from environment cimport GridEnvironment, Node
from theta_star cimport RiskThetaStar

cdef class IterativeRiskThetaStar:
    def find_path(self, GridEnvironment environment, Node start, Node goal, float target=5e-6, int niter=50,
                  atol=None, bracket=None):
        atol = atol if atol is not None else np.power(10, np.log10(target) - 2)
        bracket = bracket if bracket is not None else (
            np.power(10, np.log10(target) - 3), np.power(10, np.log10(target) + 3))
        cdef np.ndarray grid = environment.grid.copy()

        def f(float thres):
            path = RiskThetaStar.find_path(environment, start, goal, thres)
            return abs(get_path_risk_sum(path, grid) - target)

        cdef float res = minimize_scalar(f, bracket=bracket, tol=atol, options=dict(maxiter=niter)).x

        return RiskThetaStar.find_path(environment, start, goal, res)
