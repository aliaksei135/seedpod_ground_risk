import unittest

import matplotlib.pyplot as mpl

from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node
from tests.pathfinding.test_data import *


def make_path(algo: Algorithm, env: GridEnvironment, start: Node, end: Node, **kwargs):
    return algo.find_path(env, start, end, **kwargs)


def plot_path(path, env):
    fig = mpl.figure()
    ax = fig.add_subplot(111)
    if type(path[0]) is Node:
        ax.plot([n.position[1] for n in path], [n.position[0] for n in path], color='red')
    elif type(path[0]) is tuple:
        ax.plot([n[1] for n in path], [n[0] for n in path], color='red')
    if type(env) is GridEnvironment:
        im = ax.imshow(env.grid)
    elif type(env) is np.ndarray:
        im = ax.imshow(env)
    fig.colorbar(im, ax=ax)
    fig.show()


class PathfindingTestCase(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.small_deadend_environment = GridEnvironment(SMALL_DEADEND_TEST_GRID, diagonals=True)
        self.small_diag_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=True)
        self.small_no_diag_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=False)
        self.large_diag_environment = GridEnvironment(LARGE_TEST_GRID, diagonals=True)
        self.large_no_diag_environment = GridEnvironment(LARGE_TEST_GRID, diagonals=False)
        self.risk_square_environment = GridEnvironment(TEST_RISK_SQUARE_GRID, diagonals=False)
        self.risk_circle_environment = GridEnvironment(TEST_RISK_CIRCLE_GRID, diagonals=False)
        self.risk_circle2_environment = GridEnvironment(TEST_RISK_CIRCLE2_GRID, diagonals=False)
