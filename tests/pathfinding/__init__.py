import unittest

from seedpod_ground_risk.pathfinding.environment import GridEnvironment
from tests.pathfinding.test_data import *


class PathfindingTestCase(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.small_deadend_environment = GridEnvironment(SMALL_DEADEND_TEST_GRID, diagonals=True)
        self.small_diag_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=True)
        self.small_no_diag_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=False)
        self.large_diag_environment = GridEnvironment(LARGE_TEST_GRID, diagonals=True)
        self.risk_square_environment = GridEnvironment(TEST_RISK_SQUARE_GRID, diagonals=False)
        self.risk_circle_environment = GridEnvironment(TEST_RISK_CIRCLE_GRID, diagonals=False)
        self.risk_circle2_environment = GridEnvironment(TEST_RISK_CIRCLE2_GRID, diagonals=False)
