import unittest

import numpy as np

from seedpod_ground_risk.pathfinding.bresenham import make_line


class BresenhamCase(unittest.TestCase):

    def test_first_quadrant(self):
        start = [0, 1]  # x, y
        end = [6, 4]  # x, y

        path = make_line(*start, *end)

        expected = np.array([[1, 0],
                             [1, 1],
                             [2, 2],
                             [2, 3],
                             [3, 4],
                             [3, 5],
                             [4, 6]])
        result = (path == expected).all() or (path == np.flipud(expected)).all()
        self.assertTrue(result, 'First Quadrant path incorrect')

    def test_second_quadrant(self):
        start = [0, 1]  # x, y
        end = [-6, 4]  # x, y

        path = make_line(*start, *end)

        expected = np.array([[1, 0],
                             [2, -1],
                             [2, -2],
                             [3, -3],
                             [3, -4],
                             [4, -5],
                             [4, -6]])
        result = (path == expected).all() or (path == np.flipud(expected)).all()
        self.assertTrue(result, 'Second Quadrant path incorrect')

    def test_third_quadrant(self):
        start = [0, -1]  # x, y
        end = [-6, -4]  # x, y

        path = make_line(*start, *end)

        expected = np.array([[-1, 0],
                             [-2, -1],
                             [-2, -2],
                             [-3, -3],
                             [-3, -4],
                             [-4, -5],
                             [-4, -6]])
        result = (path == expected).all() or (path == np.flipud(expected)).all()
        self.assertTrue(result, 'Third Quadrant path incorrect')

    def test_fourth_quadrant(self):
        start = [0, -1]  # x, y
        end = [6, -4]  # x, y

        path = make_line(*start, *end)

        expected = np.array([[-1, 0],
                             [-1, 1],
                             [-2, 2],
                             [-2, 3],
                             [-3, 4],
                             [-3, 5],
                             [-4, 6]])
        result = (path == expected).all() or (path == np.flipud(expected)).all()
        self.assertTrue(result, 'Fourth Quadrant path incorrect')

    def test_bounds(self):
        start = [2, 0]
        end = [4, 4]

        path = make_line(*start, *end)
        flat_points = np.ravel(path)
        result = (flat_points <= 4).all() and (flat_points >= 0).all()
        self.assertTrue(result, "Points not bounded within endpoints")

    def test_high_gradient(self):
        start = [0, 6]  # x, y
        end = [6, 0]  # x, y

        path = make_line(*start, *end)

        expected = np.array([[0, 6],
                             [1, 5],
                             [2, 4],
                             [3, 3],
                             [4, 2],
                             [5, 1],
                             [6, 0]])
        result = (path == expected).all() or (path == np.flipud(expected)).all()
        self.assertTrue(result, 'First Quadrant path incorrect')


if __name__ == '__main__':
    unittest.main()
