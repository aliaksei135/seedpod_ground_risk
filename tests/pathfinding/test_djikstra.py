import unittest

import matplotlib.pyplot as mpl
from matplotlib.gridspec import GridSpec

from seedpod_ground_risk.pathfinding import get_path_risk_mean, get_path_distance, get_path_risk_sum
from seedpod_ground_risk.pathfinding.dijkstra import Dijkstra
from seedpod_ground_risk.pathfinding.moo_ga import *
from tests.pathfinding import PathfindingTestCase, make_path
from tests.pathfinding.test_data import *


class DijkstraTestCase(PathfindingTestCase):

    def test_risk_square(self):
        start = Node((1, 1))
        end = Node((99, 99))

        algo = Dijkstra()

        path = algo.find_path(self.risk_square_environment, start, end, smooth=False)

        fig = mpl.figure()
        ax = fig.add_subplot(111)
        ax.plot([n.position[1] for n in path], [n.position[0] for n in path], color='red')
        im = ax.imshow(self.risk_square_environment.grid)
        fig.colorbar(im, ax=ax)
        fig.show()

        self.assertEqual(hash(tuple(path)), -5148357753668335358)

    def test_risk_circle(self):
        start = Node((1, 1))
        end = Node((99, 99))

        algo = Dijkstra()

        path = algo.find_path(self.risk_circle_environment, start, end, smooth=False)

        fig = mpl.figure()
        ax = fig.add_subplot(111)
        ax.plot([n.position[1] for n in path], [n.position[0] for n in path], color='red')
        im = ax.imshow(self.risk_circle_environment.grid)
        fig.colorbar(im, ax=ax)
        fig.show()

        self.assertEqual(hash(tuple(path)), 5877875642102134190)

    def test_risk_circle2(self):
        start = Node((1, 1))
        end = Node((99, 99))

        algo = Dijkstra()

        path = algo.find_path(self.risk_circle2_environment, start, end, smooth=False)

        fig = mpl.figure()
        ax = fig.add_subplot(111)
        ax.plot([n.position[1] for n in path], [n.position[0] for n in path], color='red')
        im = ax.imshow(self.risk_circle2_environment.grid)
        fig.colorbar(im, ax=ax)
        fig.show()

        self.assertEqual(hash(tuple(path)), -3496425298084146625)

    def test_risk_circle2_thres_sweep(self):
        start = Node((1, 1))
        end = Node((99, 99))
        # start = Node((500, 10))
        # end = Node((100, 800))
        algo = Dijkstra()
        env = self.risk_circle2_environment
        test_points = 10

        truth_hashes = [-8634747763696548848,
                        6281777845410888869,
                        3754318523562311322,
                        8212258328002924383]

        asserting = test_points == len(truth_hashes)

        risk_sums = [np.inf]
        risk_means = []
        distances = []

        thresholds = np.logspace(-6, -9, test_points)

        for idx, thres in enumerate(thresholds):
            with self.subTest():
                path = make_path(algo, env, start, end, smooth=False, thres=thres)
                # plot_path(path, env)
                if asserting:
                    self.assertEqual(hash(tuple(path)), truth_hashes[idx],
                                     msg=f'Path for thres={thres} incorrect')

                risk_sum = get_path_risk_sum(path, env)
                if asserting and risk_sums[-1] <= risk_sum:
                    self.fail(f"Risk Sum not decreasing with lower risk threshold, {risk_sums[-1]}!<={risk_sum}")

                risk_sums.append(risk_sum)
                risk_means.append(get_path_risk_mean(path, env))
                distances.append(get_path_distance(path))
        risk_sums = risk_sums[1:]

        gs = GridSpec(4, 1, hspace=0.9)
        fig = mpl.figure()
        ax1 = fig.add_subplot(gs[0, :])
        ax2 = fig.add_subplot(gs[1, :])
        ax3 = fig.add_subplot(gs[2, :])
        ax4 = fig.add_subplot(gs[3, :])
        ax1.grid(which='both')
        ax2.grid(which='both')
        ax3.grid(which='both')
        ax4.grid(which='both')
        ax1.set_xscale('log')
        ax1.set_yscale('log')
        ax2.set_xscale('log')
        ax2.set_yscale('log')
        ax3.set_xscale('log')
        ax4.set_xscale('log')
        ax4.set_yscale('log')

        ax1.set_title('Path Risk Integral')
        ax2.set_title('Path Risk Mean')
        ax3.set_title('Path Distance')
        ax4.set_title('Path Mean Risk/Distance')
        ax4.set_xlabel("Input Threshold")

        ax1.plot(thresholds, risk_sums, c='blue', label='Path Risk Integrals')
        ax2.plot(thresholds, risk_means, c='green', label='Path Risk Integrals')
        ax3.plot(thresholds, distances, c='red', label='Path Distances')
        ax4.plot(thresholds, np.array(risk_sums) / np.array(distances), c='yellow', label='Path Mean Risk/Distances')

        fig.suptitle("Input Threshold Effects")
        fig.show()

    def test_large_env_with_diagonals(self):
        start = Node((500, 10))
        end = Node((100, 800))

        grid = self.large_diag_environment.grid

        algo = Dijkstra()

        path = algo.find_path(self.large_diag_environment, start, end)
        self.assertIsNotNone(path, 'Failed to find possible path')

        print("Integral: " + str(np.sum(grid[[n.position for n in path]])))

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
