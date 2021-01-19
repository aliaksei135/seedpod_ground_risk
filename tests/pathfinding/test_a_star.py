import unittest

from seedpod_ground_risk.pathfinding.a_star import GridAStar
from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node
from tests.pathfinding.test_data import SMALL_TEST_GRID


class AStarTestCase(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.diag_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=True, pruning=False)
        self.no_diag_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=False, pruning=False)
        self.algo = GridAStar()
        self.start = Node(0, 0, 0)
        self.end = Node(4, 4, 0)

    def test_direct_no_diagonals(self):
        """
        Test simplest case of direct path on small grid with no diagonals ignoring node values
        """
        path = self.algo.find_path(self.no_diag_environment, self.start, self.end)

        self.assertEqual(path[0], self.start, 'Start node not included in path')
        self.assertEqual(path[-1], self.end, 'Goal node not included in path')
        # Could take either zigzag path both of which are correct but have same path length
        # There are no other paths of length 9 other than these zigzag paths, so tests for either of these
        self.assertEqual(len(path), 9, 'Path wrong length (not direct?)')

    def test_direct_with_diagonals(self):
        """
        Test simplest case of direct path on small grid with diagonals ignoring node values
        """
        path = self.algo.find_path(self.diag_environment, self.start, self.end)

        self.assertEqual(path[0], self.start, "Start node not included in path")
        self.assertEqual(path[-1], self.end, 'Goal node not included in path')
        self.assertEqual(path, [
            Node(0, 0, 0),
            Node(1, 1, 5),
            Node(2, 2, 45),
            Node(3, 3, 30),
            Node(4, 4, 0)
        ],
                         "Incorrect path")

    def test_start_is_goal(self):
        """
        Test case of start and goal being the same node
        """
        path = self.algo.find_path(self.no_diag_environment, self.start, self.start)

        self.assertEqual(path, [self.start])

    def test_goal_unreachable(self):
        pass


if __name__ == '__main__':
    unittest.main()
