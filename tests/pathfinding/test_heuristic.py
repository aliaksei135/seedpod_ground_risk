import unittest

from seedpod_ground_risk.pathfinding.environment import Node, GridEnvironment
from seedpod_ground_risk.pathfinding.heuristic import EuclideanHeuristic, ManhattanHeuristic, EuclideanRiskHeuristic
from tests.pathfinding.test_data import SMALL_TEST_GRID


class EuclideanHeuristicTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.heuristic = EuclideanHeuristic().h

    def test_positive(self):
        """
        Test both dimension differences being positive
        """
        n1 = Node(0, 0, 0)
        n2 = Node(1, 1, 0)
        cost = self.heuristic(n1, n2)
        self.assertEqual(cost, 2 ** 0.5, 'Wrong cost')

    def test_negative(self):
        """
        Test both dimensions being negative
        """
        n1 = Node(0, 0, 0)
        n2 = Node(-1, -1, 0)
        cost = self.heuristic(n1, n2)
        self.assertEqual(cost, 2 ** 0.5, 'Wrong cost')

    def test_mixed(self):
        """
        Test mixed sign dimensions
        """
        n1 = Node(0, 0, 0)
        n2 = Node(-1, 1, 0)
        n3 = Node(1, -1, 0)
        cost2 = self.heuristic(n1, n3)
        cost1 = self.heuristic(n1, n2)
        self.assertEqual(cost1, cost2, "Wrong cost")
        self.assertEqual(cost1, 2 ** 0.5, 'Wrong cost')


class ManhattanHeuristicTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.heuristic = ManhattanHeuristic().h

    def test_positive(self):
        """
        Test both dimension differences being positive
        """
        n1 = Node(0, 0, 0)
        n2 = Node(1, 1, 0)
        cost = self.heuristic(n1, n2)
        self.assertEqual(cost, 2, 'Wrong cost')

    def test_negative(self):
        """
        Test both dimensions being negative
        """
        n1 = Node(0, 0, 0)
        n2 = Node(-1, -1, 0)
        cost = self.heuristic(n1, n2)
        self.assertEqual(cost, 2, 'Wrong cost')

    def test_mixed(self):
        """
        Test mixed sign dimensions
        """
        n1 = Node(0, 0, 0)
        n2 = Node(-1, 1, 0)
        n3 = Node(1, -1, 0)
        cost2 = self.heuristic(n1, n3)
        cost1 = self.heuristic(n1, n2)
        self.assertEqual(cost1, cost2, "Wrong cost")
        self.assertEqual(cost1, 2, 'Wrong cost')


class EuclideanRiskHeuristicTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.env = GridEnvironment(SMALL_TEST_GRID)
        self.heuristic = EuclideanRiskHeuristic(self.env, risk_to_dist_ratio=1)

    def test_positive(self):
        """
        Test both dimension differences being positive
        """
        n1 = Node(0, 0, 0)
        n2 = Node(1, 1, 5)
        cost = self.heuristic.h(n1, n2)
        self.assertEqual(cost, 2.5 + 2 ** 0.5, 'Wrong cost')


if __name__ == '__main__':
    unittest.main()
