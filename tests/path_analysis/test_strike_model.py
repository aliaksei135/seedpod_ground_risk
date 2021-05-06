import unittest

import numpy as np

from seedpod_ground_risk.path_analysis.harm_models.strike_model import StrikeModel, get_lethal_area


class StrikeModelTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.test_shape = (100, 100)
        self.pix_area = 20 * 20
        self.test_pdf = np.random.random(self.test_shape)

    def test_lethal_area_ranges(self):
        angles = np.deg2rad(np.linspace(1, 90))
        la = get_lethal_area(angles, 1)
        prop_la = la / self.pix_area

        self.assertLessEqual(prop_la.max(), 1)
        self.assertGreaterEqual(prop_la.min(), 0)

    def test_max_range(self):
        max_grid = np.full(self.test_shape, 1)

        sm = StrikeModel(max_grid, self.pix_area, 2, np.deg2rad(30))
        out = sm.transform(max_grid)

        self.assertLessEqual(out.max(), 1)
        self.assertGreaterEqual(out.min(), 0)

    def test_min_range(self):
        min_grid = np.full(self.test_shape, 0)

        sm = StrikeModel(min_grid, self.pix_area, 2, np.deg2rad(30))
        out = sm.transform(min_grid)

        self.assertLessEqual(out.max(), 1)
        self.assertGreaterEqual(out.min(), 0)

    def test_array_inputs(self):
        angles = np.random.random(self.test_shape) * 2
        pop_density = np.random.random(self.test_shape) * 6
        sm = StrikeModel(pop_density, self.pix_area, 2, angles)
        out = sm.transform(self.test_pdf)
        self.assertTupleEqual(self.test_shape, out.shape)


if __name__ == '__main__':
    unittest.main()
