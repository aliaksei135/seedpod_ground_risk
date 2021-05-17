import unittest
from functools import partial

from seedpod_ground_risk.pathfinding.moo_ga import *
from tests.pathfinding.test_data import *


class MOOGATestCase(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.small_deadend_environment = GridEnvironment(SMALL_DEADEND_TEST_GRID, diagonals=True)
        self.small_diag_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=True)
        self.small_no_diag_environment = GridEnvironment(SMALL_TEST_GRID, diagonals=False)
        self.large_diag_environment = GridEnvironment(LARGE_TEST_GRID, diagonals=True)

    def test_large_env_with_diagonals(self):
        start = Node((500, 10))
        end = Node((100, 800))

        grid = self.large_diag_environment.grid
        max_dist = np.sqrt((grid.shape[0] ** 2) + (grid.shape[1] ** 2))
        grid_max = grid.max()
        fitness_funcs = [
            partial(fitness_min_risk, grid, grid_max),
            partial(fitness_min_manhattan_length, max_dist)
        ]
        fitness_weights = [
            1e11,
            1
        ]

        algo = GeneticAlgorithm(fitness_funcs, fitness_weights)

        path = algo.find_path(self.large_diag_environment, start, end)
        self.assertIsNotNone(path, 'Failed to find possible path')

        import matplotlib.pyplot as mpl
        fig, (ax1, ax2) = mpl.subplots(2, 1,
                                       gridspec_kw={
                                           # 'width_ratios': [2, 1],
                                           'height_ratios': [10, 1]})
        g = ax1.matshow(grid)
        fig.colorbar(g, ax=ax1)
        ax1.plot([n.position[1] for n in path], [n.position[0] for n in path], color='magenta')
        ys = []
        for idx in range(len(path[:-1])):
            n0 = path[idx].position
            n1 = path[idx + 1].position
            l = line(n0[0], n0[1], n1[0], n1[1])
            ys.append(grid[l[0], l[1]])
        ys = np.hstack(ys)
        ax2.plot(ys)

        mpl.tight_layout()
        fig.show()


if __name__ == '__main__':
    unittest.main()
