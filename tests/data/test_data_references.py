import unittest

from seedpod_ground_risk.data import *


class DataRefsTestCase(unittest.TestCase):

    def test_aircraft_list_filepath(self):
        aircraft_list = aircraft_list_filepath()
        aircraft_fp_win = 'static_data\\aircraft_list.json'
        aircraft_fp_lin = 'static_data/aircraft_list.json'
        self.assertIn(aircraft_list, {aircraft_fp_lin, aircraft_fp_win})

    def test_england_wa_2011_clipped_filepath(self):
        england_wa_2011_clipped = england_wa_2011_clipped_filepath()
        england_wa_2011_clipped_fp_win = 'static_data\\england_wa_2011_clipped.shp'
        england_wa_2011_clipped_fp_lin = 'static_data/england_wa_2011_clipped.shp'
        self.assertIn(england_wa_2011_clipped, {england_wa_2011_clipped_fp_lin, england_wa_2011_clipped_fp_win})

    def test_nhaps_data_filepath(self):
        nhaps_filepath = nhaps_data_filepath()
        nhaps_data_fp_win = 'static_data\\nhaps.json'
        nhaps_data_fp_lin = 'static_data/nhaps.json'
        self.assertIn(nhaps_filepath, {nhaps_data_fp_lin, nhaps_data_fp_win})

    def test_density_filepath(self):
        density = density_filepath()
        density_fp_win = 'static_data\\density.csv'
        density_fp_lin = 'static_data/density.csv'
        self.assertIn(density, {density_fp_lin, density_fp_win})

    def test_traffic_count_filepath(self):
        traffic_count = traffic_count_filepath()
        traffic_count_fp_win = 'static_data\\dft_traffic_counts_aadf.csv'
        traffic_count_fp_lin = 'static_data/dft_traffic_counts_aadf.csv'
        self.assertIn(traffic_count, {traffic_count_fp_lin, traffic_count_fp_win})

    def test_road_geometry_filepath(self):
        road_geometry = road_geometry_filepath()
        road_geometry_fp_win = 'static_data\\2018-MRDB-minimal.shp'
        road_geometry_fp_lin = 'static_data/2018-MRDB-minimal.shp'
        self.assertIn(road_geometry, {road_geometry_fp_lin, road_geometry_fp_win})

    def test_relative_variation_filepath(self):
        rel_variation = relative_variation_filepath()
        relative_variation_fp_win = 'static_data\\tra0307.ods'
        relative_variation_fp_lin = 'static_data/tra0307.ods'
        self.assertIn(rel_variation, {relative_variation_fp_lin, relative_variation_fp_win})
