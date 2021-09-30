import platform
import unittest

from seedpod_ground_risk.data import *


class DataRefsTestCase(unittest.TestCase):

    def test_aircraft_list_filepath(self):
        aircraft_list = aircraft_list_filepath()
        if platform.system() == "Windows":
            aircraft_fp_win = 'static_data\\aircraft_list.json'
            self.assertEqual(aircraft_list, aircraft_fp_win)
        elif platform.system() == "Linux":
            aircraft_fp_lin = 'static_data/aircraft_list.json'
            self.assertEqual(aircraft_list, aircraft_fp_lin)

    def test_england_wa_2011_clipped_filepath(self):
        england_wa_2011_clipped = england_wa_2011_clipped_filepath()
        if platform.system() == "Windows":
            england_wa_2011_clipped_fp_win = 'static_data\\england_wa_2011_clipped.shp'
            self.assertEqual(england_wa_2011_clipped, england_wa_2011_clipped_fp_win)
        elif platform.system() == "Linux":
            england_wa_2011_clipped_fp_lin = 'static_data/england_wa_2011_clipped.shp'
            self.assertEqual(england_wa_2011_clipped, england_wa_2011_clipped_fp_lin)

    def test_nhaps_data_filepath(self):
        nhaps_filepath = nhaps_data_filepath()
        if platform.system() == "Windows":
            nhaps_data_fp_win = 'static_data\\nhaps.json'
            self.assertEqual(nhaps_filepath, nhaps_data_fp_win)
        elif platform.system() == "Linux":
            nhaps_data_fp_lin = 'static_data/nhaps.json'
            self.assertEqual(nhaps_filepath, nhaps_data_fp_lin)

    def test_density_filepath(self):
        density = density_filepath()
        if platform.system() == "Windows":
            density_fp_win = 'static_data\\density.csv'
            self.assertEqual(density, density_fp_win)
        elif platform.system() == "Linux":
            density_fp_lin = 'static_data/density.csv'
            self.assertEqual(density, density_fp_lin)

    def test_traffic_count_filepath(self):
        traffic_count = traffic_count_filepath()
        if platform.system() == "Windows":
            traffic_count_fp_win = 'static_data\\dft_traffic_counts_aadf.csv'
            self.assertEqual(traffic_count, traffic_count_fp_win)
        elif platform.system() == "Linux":
            traffic_count_fp_lin = 'static_data/dft_traffic_counts_aadf.csv'
            self.assertEqual(traffic_count, traffic_count_fp_lin)

    def test_road_geometry_filepath(self):
        road_geometry = road_geometry_filepath()
        if platform.system() == "Windows":
            road_geometry_fp_win = 'static_data\\2018-MRDB-minimal.shp'
            self.assertEqual(road_geometry, road_geometry_fp_win)
        elif platform.system() == "Linux":
            road_geometry_fp_lin = 'static_data/2018-MRDB-minimal.shp'
            self.assertEqual(road_geometry, road_geometry_fp_lin)

    def test_relative_variation_filepath(self):
        rel_variation = relative_variation_filepath()
        if platform.system() == "Windows":
            relative_variation_fp_win = 'static_data\\tra0307.ods'
            self.assertEqual(rel_variation, relative_variation_fp_win)
        elif platform.system() == "Linux":
            relative_variation_fp_lin = 'static_data/tra0307.ods'
            self.assertEqual(rel_variation, relative_variation_fp_lin)
