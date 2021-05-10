import unittest

import shapely.geometry as sg

from seedpod_ground_risk.core.utils import make_bounds_polygon


class UtilsTestCase(unittest.TestCase):

    def test_bounds_polygon_2arg(self):
        res = make_bounds_polygon((1, 5), (1, 5))
        poly = sg.Polygon([(1, 1), (1, 5), (5, 5), (5, 1)])
        # __eq__ and .equals are not the same for sg objects!
        self.assertTrue(res.equals(poly))

    def test_bounds_polygon_4arg(self):
        res = make_bounds_polygon(1, 1, 5, 5)
        poly = sg.Polygon([(1, 1), (1, 5), (5, 5), (5, 1)])
        # __eq__ and .equals are not the same for sg objects!
        self.assertTrue(res.equals(poly))


if __name__ == '__main__':
    unittest.main()
