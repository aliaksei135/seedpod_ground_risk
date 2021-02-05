import unittest

from seedpod_ground_risk.pathfinding.a_star import GridAStar, RiskGridAStar, JumpPointSearchAStar, \
    RiskJumpPointSearchAStar
from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node
from seedpod_ground_risk.pathfinding.heuristic import EuclideanRiskHeuristic
from tests.pathfinding.test_data import SMALL_TEST_GRID, LARGE_TEST_GRID, SMALL_DEADEND_TEST_GRID


class BaseAStarTestCase(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.small_deadend_environment = GridEnvironment(SMALL_DEADEND_TEST_GRID, diagonals=True, pruning=False)
        self.small_diag_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=True, pruning=False)
        self.small_no_diag_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=False, pruning=False)
        self.large_diag_environment = GridEnvironment(LARGE_TEST_GRID, diagonals=True, pruning=False)
        self.large_no_diag_environment = GridEnvironment(LARGE_TEST_GRID, diagonals=False, pruning=False)
        self.start = Node(0, 0, 0)
        self.end = Node(4, 4, 0)

    def test_start_is_goal(self):
        """
        Test case of start and goal being the same node
        """
        # Do not test base class!
        if self.__class__ is BaseAStarTestCase:
            return
        path = self.algo.find_path(self.small_diag_environment, self.start, self.start)

        self.assertEqual(path, [self.start])

    def test_goal_unreachable(self):
        """
        Test behaviour when path is impossible due to obstacles
        """
        # Do not test base class!
        if self.__class__ is BaseAStarTestCase:
            return
        path = self.algo.find_path(self.small_deadend_environment, self.start, self.end)

        self.assertEqual(path, None, "Impossible path should be None")


class GridAStarTestCase(BaseAStarTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.algo = GridAStar()

    def test_direct_no_diagonals(self):
        """
        Test simplest case of direct path on small grid with no diagonals ignoring node values
        """
        path = self.algo.find_path(self.small_no_diag_environment, self.start, self.end)

        self.assertEqual(path[0], self.start, 'Start node not included in path')
        self.assertEqual(path[-1], self.end, 'Goal node not included in path')
        # Could take either zigzag path both of which are correct but have same path length
        # There are no other paths of length 9 other than these zigzag paths, so tests for either of these
        self.assertEqual(len(path), 9, 'Path wrong length (not direct?)')

    def test_direct_with_diagonals(self):
        """
        Test simplest case of direct path on small grid with diagonals ignoring node values
        """
        path = self.algo.find_path(self.small_diag_environment, self.start, self.end)

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


class RiskGridAStarTestCase(BaseAStarTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.algo = RiskGridAStar(heuristic=EuclideanRiskHeuristic(self.small_no_diag_environment))

    def test_direct_no_diagonals(self):
        """
        Test simplest case of direct path on small grid with no diagonals ignoring node values
        """
        path = self.algo.find_path(self.small_no_diag_environment, self.start, self.end)

        self.assertEqual(path[0], self.start, 'Start node not included in path')
        self.assertEqual(path[-1], self.end, 'Goal node not included in path')
        # Could take either zigzag path both of which are correct but have same path length
        # There are no other paths of length 9 other than these zigzag paths, so tests for either of these
        self.assertEqual(len(path), 9, 'Path wrong length (not direct?)')

    def test_direct_with_diagonals(self):
        """
        Test simplest case of direct path on small grid with diagonals ignoring node values
        """
        path = self.algo.find_path(self.small_diag_environment, self.start, self.end)

        self.assertEqual(path[0], self.start, "Start node not included in path")
        self.assertEqual(path[-1], self.end, 'Goal node not included in path')
        self.assertEqual(path, [
            Node(0, 0, 0),
            Node(0, 1, 2),
            Node(1, 2, 34),
            Node(2, 2, 45),
            Node(3, 3, 30),
            Node(4, 4, 0)
        ],
                         "Incorrect path")


class JumpPointSearchAStarTestCase(BaseAStarTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.algo = JumpPointSearchAStar()

    def test_direct_no_diagonals(self):
        """
        Test simplest case of direct path on small grid with no diagonals ignoring node values
        """
        self.assertRaises(ValueError, self.algo.find_path, self.small_no_diag_environment, self.start, self.end)

    def test_direct_with_diagonals(self):
        """
        Test simplest case of direct path on small grid with diagonals ignoring node values
        """
        path = self.algo.find_path(self.small_diag_environment, self.start, self.end)

        self.assertEqual(path[0], self.start, "Start node not included in path")
        self.assertEqual(path[-1], self.end, 'Goal node not included in path')
        self.assertEqual(path, [
            Node(0, 0, 0),
            Node(4, 4, 0)
        ],
                         "Incorrect path")


class RiskJumpPointSearchAStarTestCase(BaseAStarTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.algo = RiskJumpPointSearchAStar(EuclideanRiskHeuristic(self.small_diag_environment,
                                                                    risk_to_dist_ratio=1))

    def test_direct_no_diagonals(self):
        """
        Test simplest case of direct path on small grid with no diagonals ignoring node values
        """
        self.assertRaises(ValueError, self.algo.find_path, self.small_no_diag_environment, self.start, self.end)

    def test_direct_with_diagonals(self):
        """
        Test simplest case of direct path on small grid with diagonals ignoring node values
        """
        path = self.algo.find_path(self.small_diag_environment, self.start, self.end)

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

    def test_goal_unreachable(self):
        """
        Test behaviour when path is impossible due to obstacles
        """
        algo = RiskJumpPointSearchAStar(EuclideanRiskHeuristic(self.small_deadend_environment,
                                                               risk_to_dist_ratio=1))
        path = algo.find_path(self.small_deadend_environment, self.start, self.end)

        self.assertEqual(path, None, "Impossible path should be None")

    def test_environment_mismatch(self):
        """
        Test behaviour when algorithm environment does not match that passed to the heuristic
        """
        self.assertRaises(ValueError, self.algo.find_path, self.large_diag_environment, self.start, self.end)

if __name__ == '__main__':
    unittest.main()
