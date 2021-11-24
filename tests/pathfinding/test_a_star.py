import unittest

import matplotlib.pyplot as mpl

from seedpod_ground_risk.pathfinding.a_star import *
from seedpod_ground_risk.pathfinding.heuristic import *
from seedpod_ground_risk.pathfinding.rjps_a_star import *
from tests.pathfinding import PathfindingTestCase, make_path, get_path_risk_sum


class BaseAStarTestCase(PathfindingTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.start = Node((0, 0))
        self.end = Node((4, 4))

    def test_start_is_goal(self):
        """
        Test case of start and goal being the same node
        """
        # Do not test base class!
        if self.__class__ is BaseAStarTestCase:
            return
        path = self.algo.find_path(self.small_diag_environment, self.start, self.start, smooth=True)

        self.assertEqual(path, [self.start])

    def test_goal_unreachable(self):
        """
        Test behaviour when path is impossible due to obstacles
        """
        # Do not test base class!
        if self.__class__ is BaseAStarTestCase:
            return
        path = self.algo.find_path(self.small_deadend_environment, self.start, self.end, )

        self.assertEqual(path, None, "Impossible path should be None")


class RiskGridAStarTestCase(BaseAStarTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.algo = RiskGridAStar(heuristic=ManhattanRiskHeuristic(self.small_no_diag_environment))

    def test_direct_no_diagonals(self):
        """
        Test simplest case of direct path on small grid with no diagonals ignoring node values
        """
        path = make_path(self.algo, self.small_no_diag_environment, self.start, self.end, smooth=True)

        self.assertEqual(path[0], self.start, 'Start node not included in path')
        self.assertEqual(path[-1], self.end, 'Goal node not included in path')
        # Could take either zigzag path both of which are correct but have same path length
        # There are no other paths of length 9 other than these zigzag paths, so tests for either of these
        self.assertLess(len(path), 10, 'Path wrong length (not direct?)')

    def test_direct_with_diagonals(self):
        """
        Test simplest case of direct path on small grid with diagonals ignoring node values
        """
        path = make_path(self.algo, self.small_diag_environment, self.start, self.end, smooth=True)

        self.assertEqual(path[0], self.start, "Start node not included in path")
        self.assertEqual(path[-1], self.end, 'Goal node not included in path')
        self.assertEqual(path, [
            Node((0, 0)),
            Node((2, 0)),
            Node((3, 1)),
            Node((4, 2)),
            Node((4, 3)),
            Node((4, 4))
        ],
                         "Incorrect path")

    def test_risk_block(self):
        start = Node((1, 1))
        end = Node((99, 99))
        path = make_path(self.algo, self.risk_square_environment, start, end, smooth=False)

        fig = mpl.figure()
        ax = fig.add_subplot(111)
        ax.plot([n.position[1] for n in path], [n.position[0] for n in path], color='red')
        im = ax.imshow(self.risk_square_environment.grid)
        fig.colorbar(im, ax=ax, label='Population')
        fig.show()

    def test_large_env_with_diagonals(self):
        """
        Test on realistic costmap. Used mainly for profiling code
        """
        algo = RiskGridAStar(ManhattanRiskHeuristic(self.large_diag_environment,
                                                    risk_to_dist_ratio=1))
        path = make_path(self.algo, self.large_diag_environment, Node((10, 10)), Node((490, 490)), )
        self.assertIsNotNone(path, 'Failed to find possible path')

    def test_repeatability(self):
        import matplotlib.pyplot as mpl
        import numpy as np

        start, end = Node((450, 50)), Node((100, 450))
        repeats = 2
        equal_paths = []
        rdrs = np.linspace(100, 10000, 10)
        risk_sums = []
        env = self.large_diag_environment

        def do_path(start, end, rdr):
            algo = RiskGridAStar(ManhattanRiskHeuristic(self.large_diag_environment,
                                                        risk_to_dist_ratio=rdr))
            return make_path(algo, env, start, end, )

        # def run_params(rdr):
        #     paths = [make_path(start, end, rdr) for _ in range(repeats)]
        #     equal_paths.append(all([p == paths[0] for p in paths]))
        #     if not paths[0]:
        #         return [rdr, np.inf]
        #     risk_sum = sum([self.large_diag_environment.grid[n[0], n[1]] for n in paths[0]])
        #     return [rdr, risk_sum]
        #
        # pool = ProcessPool(nodes=8)
        # params = np.array(rdrs)
        # risk_sums = pool.map(run_params, params)
        # pool.close()

        for rdr in rdrs:
            paths = [do_path(start, end, rdr) for _ in range(repeats)]
            equal_paths.append(all([p == paths[0] for p in paths]))
            if not paths[0]:
                risk_sums.append([rdr, np.inf])
                continue
            risk_sum = get_path_risk_sum(paths[0], env)
            risk_sums.append([rdr, risk_sum])

            fig = mpl.figure()
            ax = fig.add_subplot(111)
            for path in paths:
                ax.plot([n.position[1] for n in path], [n.position[0] for n in path], color='red')
            im = ax.imshow(self.large_diag_environment.grid)
            fig.colorbar(im, ax=ax, label='Population')
            ax.set_title(f'RiskA* with RDR={rdr:.4g} \n Risk sum={risk_sum:.4g}')
            fig.show()

        risk_sums = np.array(risk_sums)

        rdr_fig = mpl.figure()
        ax = rdr_fig.add_subplot(111)
        ax.scatter(risk_sums[:, 0], risk_sums[:, 1])
        # ax.set_xscale('log')
        ax.set_yscale('symlog')
        ax.set_xlabel('Risk-Distance Ratio')
        ax.set_ylabel('Path Risk sum')
        ax.set_title('Risk Grid A*')
        rdr_fig.show()
        self.assertTrue(all(equal_paths), 'Paths are not generated repeatably')


if __name__ == '__main__':
    unittest.main()
