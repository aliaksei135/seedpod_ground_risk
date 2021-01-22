import unittest

from seedpod_ground_risk.pathfinding.environment import GridEnvironment
from tests.pathfinding.test_data import SMALL_TEST_GRID, LARGE_TEST_GRID, SMALL_TEST_GRAPH_NO_DIAGONAL


class GridEnvironmentNoDiagonalsNoPruningTestCase(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.small_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=False, pruning=False)
        self.large_environment = GridEnvironment(LARGE_TEST_GRID, diagonals=False)

    def test_grid_to_graph(self):
        self.maxDiff = None
        graph = self.small_environment._generate_graph()
        self.assertEqual(len(graph), SMALL_TEST_GRID.shape[0] * SMALL_TEST_GRID.shape[1], "Graph has wrong length")
        self.assertDictEqual(SMALL_TEST_GRAPH_NO_DIAGONAL, graph, "Graph Malformed")


class GridEnvironmentNoDiagonalsWithPruningTestCase(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.small_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=False, pruning=True)
        self.large_environment = GridEnvironment(LARGE_TEST_GRID, diagonals=False)

    def test_grid_to_graph(self):
        self.maxDiff = None
        graph = self.small_environment._generate_graph()
        self.assertEqual(len(graph), SMALL_TEST_GRID.shape[0] * SMALL_TEST_GRID.shape[1] - 1, "Graph has wrong length")
        self.assertDictEqual(SMALL_TEST_GRAPH_NO_DIAGONAL, graph, "Graph Malformed")


class GridEnvironmentWithDiagonalsTestCase(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.small_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=True)
        self.large_environment = GridEnvironment(LARGE_TEST_GRID, diagonals=True)

    def test_grid_to_graph(self):
        pass


if __name__ == '__main__':
    unittest.main()
