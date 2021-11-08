import unittest

import matplotlib.pyplot as mpl

from seedpod_ground_risk.pathfinding.moo_ga import *
from seedpod_ground_risk.pathfinding.theta_star import RiskThetaStar
from tests.pathfinding import PathfindingTestCase


class RiskThetaStarTestCase(PathfindingTestCase):

    def test_risk_square(self):
        start = Node((1, 1))
        end = Node((99, 99))

        algo = RiskThetaStar()

        path = algo.find_path(self.risk_square_environment, start, end, smooth=False)

        fig = mpl.figure()
        ax = fig.add_subplot(111)
        ax.plot([n.position[1] for n in path], [n.position[0] for n in path], color='red')
        im = ax.imshow(self.risk_square_environment.grid)
        fig.colorbar(im, ax=ax)
        fig.show()

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

        algo = RiskThetaStar()

        path = algo.find_path(self.large_diag_environment, start, end, smooth=False, k=1e10)
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
