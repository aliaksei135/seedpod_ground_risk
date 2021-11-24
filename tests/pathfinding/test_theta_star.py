import unittest

import matplotlib.pyplot as mpl
from matplotlib.gridspec import GridSpec

from seedpod_ground_risk.pathfinding import *
from seedpod_ground_risk.pathfinding.moo_ga import *
from seedpod_ground_risk.pathfinding.theta_star import RiskThetaStar
from tests.pathfinding import PathfindingTestCase, make_path, plot_path


# import pyximport
#
# pyximport.install()


class RiskThetaStarTestCase(PathfindingTestCase):
    algo = RiskThetaStar()

    def test_risk_square(self):
        start = Node((1, 1))
        end = Node((99, 99))
        env = self.risk_square_environment

        path = make_path(self.algo, env, start, end, 1e-8)

        plot_path(path, env)

        self.assertEqual(hash(tuple(path)), -7538073030527901319)

    def test_risk_circle(self):
        start = Node((1, 1))
        end = Node((99, 99))
        env = self.risk_circle_environment

        path = self.algo.find_path(env, start, end, 1e-8)
        # path = make_path(self.algo, env, start, end, float(1e-7))

        plot_path(path, env)

        self.assertEqual(hash(tuple(path)), 419418873336358930)

    def test_risk_circle2(self):
        start = Node((1, 1))
        end = Node((99, 99))
        env = self.risk_circle2_environment

        path = self.algo.find_path(env, start, end, 1e-8)

        plot_path(path, env)
        print(get_path_risk_sum(path, env))

        self.assertEqual(hash(tuple(path)), -3485535347631114531)

    def test_risk_circle2_thres_sweep(self):
        start = Node((1, 1))
        end = Node((99, 99))
        # start = Node((500, 10))
        # end = Node((100, 800))
        env = self.risk_circle2_environment
        test_points = 4

        truth_hashes = [-1862458939195207405,
                        -1771228379410564313,
                        -3485535347631114531,
                        -1656545278618703179]

        asserting = test_points == len(truth_hashes)

        risk_sums = [np.inf]
        risk_means = []
        distances = []

        thresholds = np.logspace(-6, -9, test_points)

        for idx, thres in enumerate(thresholds):
            with self.subTest():
                path = self.algo.find_path(env, start, end, thres)
                plot_path(path, env)
                if asserting:
                    self.assertEqual(hash(tuple(path)), truth_hashes[idx],
                                     msg=f'Path for {thres} incorrect')

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

    def test_iterative_solving(self):
        # start = Node((1, 1))
        # end = Node((99, 99))
        start = Node((500, 10))
        end = Node((100, 800))
        algo = RiskThetaStar()
        # env = self.risk_circle2_environment
        env = self.large_no_diag_environment
        # grid = env
        n_iter = 50
        rit = 5e-6
        tol = np.power(10, np.log10(rit) - 2)
        bracket = (np.power(10, np.log10(rit) - 3), np.power(10, np.log10(rit) + 3))

        ns = []
        rs_ns = []

        def f(thres):
            ns.append(thres)
            path = algo.find_path(env, start, end, thres=thres)
            if path is None:
                return np.inf
            rs = get_path_risk_sum(path, env)
            err = abs(rs - rit)
            rs_ns.append(err)
            return err

        # res = root_scalar(f, method='ridder', bracket=(1e-20, 1e-2))
        # res = minimize_scalar(f, method='brent', bracket=bracket, tol=tol, options=dict(maxiter=n_iter))
        # res = minimize(f, rit, bounds=[(1e-15, 1)], tol=tol,
        #       options = dict(maxiter=n_iter))

        # conv_thres = res.x
        # conv_path = algo.find_path(env, start, end, thres=conv_thres)
        # print('Converged path risk sum: ', get_path_risk_sum(conv_path, env))
        # plot_path(conv_path, env)

        [f(t) for t in np.logspace(-9, -6)]

        # gs = GridSpec(1, 1)
        fig = mpl.figure()
        ax0 = fig.add_subplot(111)
        ax0.grid(which='both')
        ax0.set_yscale('log')
        ax0.set_xscale('log')
        ax0.scatter(ns, rs_ns)
        ax0.set_xlabel('Threshold')
        ax0.set_ylabel('Error')
        # ax0.axhline(rit, c='r')
        # ax0.axvline(conv_thres, c='g')
        fig.show()

    def test_large_env_with_diagonals(self):
        start = Node((500, 10))
        end = Node((100, 800))
        env = self.large_no_diag_environment

        path = self.algo.find_path(env, start, end, 1e-8)

        plot_path(path, env)

        self.assertEqual(hash(tuple(path)), 7734416887777391773)


if __name__ == '__main__':
    unittest.main()
