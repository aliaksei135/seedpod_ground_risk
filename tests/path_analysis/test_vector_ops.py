import unittest

import numpy as np

from seedpod_ground_risk.path_analysis.utils import rotate_2d, bearing_to_angle


class VectorRotationTestCase(unittest.TestCase):

    def test_first_quad(self):
        """
        Test rotation of vectors. Used in transformation between frames
        """
        theta = np.deg2rad(45)
        vec = np.array([0, 1])  # y, x order
        out = rotate_2d(vec, theta)
        val = np.sqrt(2) / 2
        np.testing.assert_array_almost_equal(out, np.array([val, val]), 10)

    def test_sec_quad(self):
        """
        Test rotation of vectors. Used in transformation between frames
        """
        theta = np.deg2rad(45)
        vec = np.array([1, 0])  # y, x order
        out = rotate_2d(vec, theta)
        val = np.sqrt(2) / 2
        np.testing.assert_array_almost_equal(out, np.array([val, -val]), 10)

    def test_third_quad(self):
        """
        Test rotation of vectors. Used in transformation between frames
        """
        theta = np.deg2rad(45)
        vec = np.array([0, -1])  # y, x order
        out = rotate_2d(vec, theta)
        val = np.sqrt(2) / 2
        np.testing.assert_array_almost_equal(out, np.array([-val, -val]), 10)

    def test_fourth_quad(self):
        """
        Test rotation of vectors. Used in transformation between frames
        """
        theta = np.deg2rad(45)
        vec = np.array([-1, 0])  # y, x order
        out = rotate_2d(vec, theta)
        val = np.sqrt(2) / 2
        np.testing.assert_array_almost_equal(out, np.array([-val, val]), 10)

    def test_negative_theta(self):
        theta = np.deg2rad(-45)
        vec = np.array([-1, 0])  # y, x order
        out = rotate_2d(vec, theta)
        val = np.sqrt(2) / 2
        np.testing.assert_array_almost_equal(out, np.array([-val, val]), 1e-14)

    def test_over_2pi(self):
        theta = np.deg2rad(45) + (2 * np.pi)
        vec = np.array([0, 1])  # y, x order
        out = rotate_2d(vec, theta)
        val = np.sqrt(2) / 2
        np.testing.assert_array_almost_equal(out, np.array([val, val]), 1e-14)


class BearingRotationTestCase(unittest.TestCase):

    def test_first_quad(self):
        self.assertEqual(bearing_to_angle(np.pi / 4), np.pi / 4)
        self.assertEqual(bearing_to_angle(45, is_rad=False), 45)

        self.assertEqual(bearing_to_angle(np.pi / 2), 0)
        self.assertEqual(bearing_to_angle(90, is_rad=False), 0)

        self.assertEqual(bearing_to_angle(0), np.pi / 2)
        self.assertEqual(bearing_to_angle(0, is_rad=False), 90)

        self.assertEqual(bearing_to_angle(2 * np.pi), np.pi / 2)
        self.assertEqual(bearing_to_angle(360, is_rad=False), 90)

    def test_second_quad(self):
        self.assertEqual(bearing_to_angle(np.pi + 3 * np.pi / 4), 3 * np.pi / 4)
        self.assertEqual(bearing_to_angle(315, is_rad=False), 135)

        self.assertEqual(bearing_to_angle(np.pi + np.pi / 2), np.pi)
        self.assertEqual(bearing_to_angle(270, is_rad=False), 180)

    def test_third_quad(self):
        self.assertEqual(bearing_to_angle(np.pi + np.pi / 4), np.pi + np.pi / 4)
        self.assertEqual(bearing_to_angle(225, is_rad=False), 225)

        self.assertEqual(bearing_to_angle(np.pi), np.pi + np.pi / 2)
        self.assertEqual(bearing_to_angle(180, is_rad=False), 270)

    def test_fourth_quad(self):
        self.assertEqual(bearing_to_angle(3 * np.pi / 4), np.pi + 3 * np.pi / 4)
        self.assertEqual(bearing_to_angle(135, is_rad=False), 315)


if __name__ == '__main__':
    unittest.main()
