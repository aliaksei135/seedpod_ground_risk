import unittest

import numpy as np

from seedpod_ground_risk.path_analysis.utils import rotate_2d


class VectorRotationTestCase(unittest.TestCase):

    def test_first_quad(self):
        """
        Test rotation of vectors. Used in transformation between frames
        """
        theta = np.deg2rad(45)
        vec = np.array([0, 1])  # y, x order
        out = rotate_2d(vec, theta)
        val = np.sqrt(2) / 2
        np.testing.assert_array_equal(out, np.array([val, val]))

    def test_sec_quad(self):
        """
        Test rotation of vectors. Used in transformation between frames
        """
        theta = np.deg2rad(45)
        vec = np.array([1, 0])  # y, x order
        out = rotate_2d(vec, theta)
        val = np.sqrt(2) / 2
        np.testing.assert_array_equal(out, np.array([val, -val]))

    def test_third_quad(self):
        """
        Test rotation of vectors. Used in transformation between frames
        """
        theta = np.deg2rad(45)
        vec = np.array([0, -1])  # y, x order
        out = rotate_2d(vec, theta)
        val = np.sqrt(2) / 2
        np.testing.assert_array_equal(out, np.array([-val, -val]))

    def test_fourth_quad(self):
        """
        Test rotation of vectors. Used in transformation between frames
        """
        theta = np.deg2rad(45)
        vec = np.array([-1, 0])  # y, x order
        out = rotate_2d(vec, theta)
        val = np.sqrt(2) / 2
        np.testing.assert_array_equal(out, np.array([-val, val]))

    def test_negative_theta(self):
        theta = np.deg2rad(-45)
        vec = np.array([-1, 0])  # y, x order
        out = rotate_2d(vec, theta)
        val = np.sqrt(2) / 2
        np.testing.assert_array_almost_equal(out, np.array([-val, val]))

    def test_over_2pi(self):
        theta = np.deg2rad(45) + (2 * np.pi)
        vec = np.array([0, 1])  # y, x order
        out = rotate_2d(vec, theta)
        val = np.sqrt(2) / 2
        np.testing.assert_array_almost_equal(out, np.array([val, val]))


if __name__ == '__main__':
    unittest.main()
