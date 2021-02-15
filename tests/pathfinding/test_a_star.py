import unittest

from seedpod_ground_risk.pathfinding.a_star import *
from seedpod_ground_risk.pathfinding.heuristic import *
from seedpod_ground_risk.pathfinding.rjps_a_star import *
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

    def test_large_env_with_diagonals(self):
        """
        Test on realistic costmap. Used mainly for profiling code
        """
        algo = RiskJumpPointSearchAStar(EuclideanRiskHeuristic(self.large_diag_environment,
                                                               risk_to_dist_ratio=1))
        path = algo.find_path(self.large_diag_environment, Node(10, 10, 0), Node(392, 392, 0))
        self.assertIsNotNone(path, 'Failed to find possible path')

    def test_repeatability(self):
        import matplotlib.pyplot as mpl
        import numpy as np

        start, end = Node(10, 10, 0), Node(350, 250, 0)
        repeats = 2
        equal_paths = []
        rdrs = np.logspace(-11, 11, 10)
        risk_sums = []

        def make_path(start, end, rdr):
            algo = RiskGridAStar(EuclideanRiskHeuristic(self.large_diag_environment,
                                                        risk_to_dist_ratio=rdr))
            return algo.find_path(self.large_diag_environment, start, end)

        def run_params(rdr):
            paths = [make_path(start, end, rdr) for _ in range(repeats)]
            equal_paths.append(all([p == paths[0] for p in paths]))
            if not paths[0]:
                return [rdr, np.inf]
            risk_sum = sum([n.n for n in paths[0]])
            return [rdr, risk_sum]

        # pool = ProcessPool(nodes=8)
        # params = np.array(rdrs)
        # risk_sums = pool.map(run_params, params)

        for rdr in rdrs:
            paths = [make_path(start, end, rdr) for _ in range(repeats)]
            equal_paths.append(all([p == paths[0] for p in paths]))
            if not paths[0]:
                # print('Path failed')
                risk_sums.append([rdr, np.inf])
                continue
            risk_sum = sum([n.n for n in paths[0]])
            risk_sums.append([rdr, risk_sum])

            fig = mpl.figure()
            ax = fig.add_subplot(111)
            for path in paths:
                ax.plot([n.x for n in path], [n.y for n in path], color='red')
            im = ax.imshow(self.large_no_diag_environment.grid)
            fig.colorbar(im, ax=ax, label='Population')
            ax.set_title(f'RiskA* with RDR={rdr:.4g} \n Risk sum={risk_sum:.4g}')
            fig.show()

        risk_sums = np.array(risk_sums)

        rdr_fig = mpl.figure()
        ax = rdr_fig.add_subplot(111)
        ax.scatter(risk_sums[:, 0], risk_sums[:, 1])
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel('Risk-Distance Ratio')
        ax.set_ylabel('Path Risk sum')
        ax.set_title('Risk Grid A*')
        rdr_fig.show()
        self.assertTrue(all(equal_paths), 'Paths are not generated repeatably')


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

    def test_large_env_with_diagonals(self):
        """
        Test on realistic costmap. Used mainly for profiling code
        """
        import matplotlib.pyplot as mpl

        algo = RiskJumpPointSearchAStar(EuclideanRiskHeuristic(self.large_diag_environment,
                                                               risk_to_dist_ratio=1))
        path = algo.find_path(self.large_diag_environment, Node(10, 10, 0), Node(392, 392, 0))
        risk_sum = sum([n.y for n in path])

        fig = mpl.figure()
        ax = fig.add_subplot(111)
        ax.plot([n.x for n in path], [n.y for n in path], color='red')
        im = ax.imshow(self.large_diag_environment.grid)
        fig.colorbar(im, ax=ax)
        ax.set_title(f'Risk JPS A* RDR=1, JG=0, JL=200 \n Risk sum={risk_sum:.4g}')
        fig.show()

        self.assertIsNotNone(path, 'Failed to find possible path')

    def test_repeatability(self):
        import matplotlib.pyplot as mpl
        import numpy as np
        from pathos.multiprocessing import ProcessPool
        from itertools import product

        start, end = Node(10, 10, 0), Node(350, 250, 0)
        repeats = 2
        equal_paths = []
        rdrs = np.logspace(-10, 10, 15)
        jgs = np.linspace(0, 5000, 8)
        jls = np.linspace(0, 70, 8)

        # self.large_diag_environment.get_as_graph()

        def make_path(start, end, rdr, jg, jl):
            algo = RiskJumpPointSearchAStar(EuclideanRiskHeuristic(self.large_diag_environment,
                                                                   risk_to_dist_ratio=rdr),
                                            jump_gap=jg, jump_limit=jl)
            return algo.find_path(self.large_diag_environment, start, end)

        def run_params(rdr, jg, jl):
            paths = [make_path(start, end, rdr, jg, jl) for _ in range(repeats)]
            equal_paths.append(all([p == paths[0] for p in paths]))
            if not paths[0]:
                return [rdr, np.inf, jl, jg]
            risk_sum = sum([n.n for n in paths[0]])
            return [rdr, risk_sum, jl, jg]

        pool = ProcessPool(nodes=8)
        params = np.array(list(product(rdrs, jgs, jls)))
        risk_sums = pool.map(run_params, params[:, 0], params[:, 1], params[:, 2])

        # risk_sums = []
        # for rdr, jg, jl in product(rdrs, jgs, jls):
        #     paths = [make_path(start, end, rdr, jg, jl) for _ in range(repeats)]
        #     equal_paths.append(all([p == paths[0] for p in paths]))
        #     if not paths[0]:
        #         risk_sums.append([rdr, np.inf, jl, jg])
        #         continue
        #     risk_sum = sum([n.n for n in paths[0]])
        #     risk_sums.append([rdr, risk_sum, jl, jg])
        #
        #     fig = mpl.figure()
        #     ax = fig.add_subplot(111)
        #     for path in paths:
        #         ax.plot([n.x for n in path], [n.y for n in path], color='red')
        #     im = ax.imshow(self.large_diag_environment.grid)
        #     fig.colorbar(im, ax=ax, label='Population')
        #     ax.set_title(f'Risk JPS A* with RDR={rdr:.4g}, JL={jl} \n Risk sum={risk_sum:.4g}')
        #     fig.show()

        risk_sums = np.array(risk_sums)

        jl_fig = mpl.figure()
        ax = jl_fig.add_subplot(111)
        sc = ax.scatter(risk_sums[:, 0], risk_sums[:, 1], c=risk_sums[:, 2])
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel('Risk-Distance Ratio')
        ax.set_ylabel('Path Risk sum')
        ax.set_title('R JPS+ A* Jump Limits')
        jl_fig.colorbar(sc, ax=ax, label='Jump Limit')
        jl_fig.show()

        jg_fig = mpl.figure()
        ax = jg_fig.add_subplot(111)
        sc = ax.scatter(risk_sums[:, 0], risk_sums[:, 1], c=risk_sums[:, 3])
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel('Risk-Distance Ratio')
        ax.set_ylabel('Path Risk sum')
        ax.set_title('R JPS+ A* Jump Gaps')
        jg_fig.colorbar(sc, ax=ax, label='Jump Gap')
        jg_fig.show()

        self.assertTrue(all(equal_paths), 'Paths are not generated repeatably')

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
