from seedpod_ground_risk.pathfinding import get_path_risk_sum
from seedpod_ground_risk.pathfinding.iterative_theta_star import IterativeRiskThetaStar
from tests.pathfinding import *


class IterativeRiskThetaStarTestCase(PathfindingTestCase):
    algo = IterativeRiskThetaStar()

    def test_risk_square(self):
        start = Node((1, 1))
        end = Node((99, 99))
        env = self.risk_square_environment

        path = self.algo.find_path(env, start, end, 1e-8)
        print('Converged path risk sum: ', get_path_risk_sum(path, env))

        plot_path(path, TEST_RISK_SQUARE_GRID)

        self.assertEqual(hash(tuple(path)), -1426980368256641227)

    def test_risk_circle(self):
        start = Node((1, 1))
        end = Node((99, 99))
        env = self.risk_circle_environment

        path = self.algo.find_path(env, start, end, 1e-8)

        plot_path(path, TEST_RISK_CIRCLE_GRID)
        print('Converged path risk sum: ', get_path_risk_sum(path, env))

        self.assertEqual(hash(tuple(path)), 7407489380230064092)

    def test_risk_circle2(self):
        start = Node((1, 1))
        end = Node((99, 99))
        env = self.risk_circle2_environment

        path = self.algo.find_path(env, start, end, 1e-6)
        print('Converged path risk sum: ', get_path_risk_sum(path, env))

        plot_path(path, TEST_RISK_CIRCLE2_GRID)

        self.assertEqual(hash(tuple(path)), -1862458939195207405)

    def test_large_env(self):
        start = Node((500, 10))
        end = Node((100, 800))
        env = self.large_no_diag_environment

        path = self.algo.find_path(env, start, end, 8e-7)
        print('Converged path risk sum: ', get_path_risk_sum(path, env))

        plot_path(path, env)

        self.assertEqual(hash(tuple(path)), 7644177961470539392)


if __name__ == '__main__':
    unittest.main()
