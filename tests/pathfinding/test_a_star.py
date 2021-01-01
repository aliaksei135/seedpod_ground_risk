import unittest

from seedpod_ground_risk.pathfinding.a_star import AStar
from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node
from seedpod_ground_risk.pathfinding.heuristic import EuclideanHeuristic
from tests.pathfinding.test_data import SMALL_TEST_GRID


class AStarTestCase(unittest.TestCase):

    def test_no_diagonals(self):
        environment = GridEnvironment(SMALL_TEST_GRID, diagonals=False)
        algo = AStar()
        start = Node(0, 0, 0)
        end = Node(4, 4, 0)
        path = algo.find_path(environment, start, end)
        self.assertEqual(path, [])

    def test_with_diagonals(self):
        environment = GridEnvironment(SMALL_TEST_GRID, diagonals=True)
        algo = AStar(heuristic=EuclideanHeuristic)
        start = Node(0, 0, 0)
        end = Node(4, 4, 0)
        path = algo.find_path(environment, start, end)
        self.assertEqual(path, [])

    def test_start_is_goal(self):
        environment = GridEnvironment(SMALL_TEST_GRID, diagonals=False)
        algo = AStar(heuristic=EuclideanHeuristic())
        start = end = Node(0, 0, 0)
        path = algo.find_path(environment, start, end)
        self.assertEqual(path, [])

    def test_goal_unreachable(self):
        pass


if __name__ == '__main__':
    unittest.main()
