import unittest

import numpy as np

from seedpod_ground_risk.layers.path_analysis_layer import snap_coords_to_grid


class GridSnappingTestCase(unittest.TestCase):

    def test_normal(self):
        grid = {
            'Latitude': np.array(list(range(11))),
            'Longitude': np.array(list(range(10, 21)))
        }
        lat = 5.1
        lon = 15.1
        lon_idx, lat_idx = snap_coords_to_grid(grid, lon, lat)

        self.assertEqual(lon_idx, 5)
        self.assertEqual(lat_idx, 5)

    def test_out_of_bounds_max(self):
        grid = {
            'Latitude': np.array(list(range(11))),
            'Longitude': np.array(list(range(10, 21)))
        }
        lat = 50.1
        lon = 55.1
        lon_idx, lat_idx = snap_coords_to_grid(grid, lon, lat)

        self.assertEqual(lon_idx, 10)
        self.assertEqual(lat_idx, 10)

    def test_out_of_bounds_min(self):
        grid = {
            'Latitude': np.array(list(range(11))),
            'Longitude': np.array(list(range(10, 21)))
        }
        lat = -50.1
        lon = -55.1
        lon_idx, lat_idx = snap_coords_to_grid(grid, lon, lat)

        self.assertEqual(lon_idx, 0)
        self.assertEqual(lat_idx, 0)


if __name__ == '__main__':
    unittest.main()
