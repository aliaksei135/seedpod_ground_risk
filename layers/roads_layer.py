import os
from time import time
from typing import NoReturn, List

import datashader as ds
import datashader.spatial.points as dsp
import geopandas as gpd
import geoviews as gv
import numpy as np
import pandas as pd
import shapely.ops as so
from holoviews.element import Geometry
from holoviews.operation.datashader import rasterize
from pyproj import Transformer
from shapely import geometry as sg

from layer import Layer

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
HOURS_OF_DAY = range(24)

TRAFFIC_COUNT_COLUMNS = ['count_point_id', 'year', 'latitude', 'longitude', 'road_name', 'pedal_cycles',
                         'two_wheeled_motor_vehicles', 'cars_and_taxis', 'buses_and_coaches',
                         'lgvs', 'all_hgvs', 'all_motor_vehicles']

TYPE_OCCUPANCY = {
    'pedal_cycles': 1,
    'two_wheeled_motor_vehicles': 1.4,
    'cars_and_taxis': 3,
    'buses_and_coaches': 40,
    'lgvs': 1.5,
    'all_hgvs': 1.6
}


def generate_week_timesteps():
    timestep_index = []
    for day in DAYS_OF_WEEK:
        for hour in HOURS_OF_DAY:
            s = day + ' ' + '{:2d}:00'.format(hour)
            timestep_index.append(s)
    return timestep_index


class RoadsLayer(Layer):
    _traffic_counts: gpd.GeoDataFrame

    def __init__(self, key, **kwargs):
        super(RoadsLayer, self).__init__(key, **kwargs)

        self.week_timesteps = generate_week_timesteps()
        self.interpolated_road_populations = None

        self._traffic_counts = gpd.GeoDataFrame()  # Traffic counts in EPSG:4326 coords
        self._roads_geometries = gpd.GeoDataFrame()  # Road Geometries in EPSG:27700 coords

    def preload_data(self) -> NoReturn:
        try:
            self.interpolated_road_populations = dsp.read_parquet(os.sep.join(('static_data', 'timed_tfc.parq.res100')))
        except FileNotFoundError:
            # Cannot find the pre-generated parquet file, so we have to generate it from scratch
            # Grab some snacks; this takes a while
            # TODO: Prevent low-spec hardware from even attempting to generate the data
            # This takes ~15mins with an i7-7700, 16GiB of RAM with 20GiB of SSD swap for good measure

            # Ingest and process static traffic counts
            self._ingest_traffic_counts()
            self._estimate_road_populations()
            # Ingest simplified road geometries
            self._ingest_road_geometries()
            # Interpolate static traffic counts along road geometries
            all_points = self._interpolate_traffic_counts(resolution=20)

            # Ingest relative weekly variations data and combine with static average traffic counts
            self._apply_relative_traffic_variations(all_points)

    def generate(self, bounds_polygon: sg.Polygon, from_cache: bool = False, hour: str = 'Monday 15:00') -> Geometry:
        t0 = time()
        bounds = bounds_polygon.bounds
        bounded_data = self.interpolated_road_populations[(self.interpolated_road_populations.lat > bounds[0]) &
                                                          (self.interpolated_road_populations.lon > bounds[1]) &
                                                          (self.interpolated_road_populations.lat < bounds[2]) &
                                                          (self.interpolated_road_populations.lon < bounds[3])]
        points = gv.Points(bounded_data[bounded_data.hour == self.week_timesteps.index(hour)],
                           kdims=['lon', 'lat'], vdims=['population']).opts(colorbar=True, tools=['hover', 'crosshair'],
                                                                            color='population')
        if self.rasterise:
            raster = rasterize(points, aggregator=ds.mean('population'),
                               dynamic=False).opts(colorbar=True, tools=['hover', 'crosshair'])
            t1 = time()
            print('Roads with raster: ', t1 - t0)
            return raster
        else:
            t1 = time()
            print('Roads no raster: ', t1 - t0)
            return points

    def clear_cache(self) -> NoReturn:
        self._traffic_counts = gpd.GeoDataFrame()
        self.interpolated_road_populations = None
        self._roads_geometries = gpd.GeoDataFrame()

    def _ingest_traffic_counts(self) -> NoReturn:
        """
        Ingest annualised average daily flow traffic counts
        Only the latest year of data is used.
        """
        # Ingest raw data
        counts_df = pd.read_csv(os.sep.join(('static_data', 'dft_traffic_counts_aadf.csv')))
        # Select only desired columns
        counts_df = counts_df[TRAFFIC_COUNT_COLUMNS]
        # Groupby year and select out only the latest year
        latest_counts_df = counts_df.groupby(['year']).get_group(counts_df.year.max())
        self._traffic_counts = gpd.GeoDataFrame(latest_counts_df,
                                                geometry=gpd.points_from_xy(
                                                    latest_counts_df.longitude,
                                                    latest_counts_df.latitude)).set_crs('EPSG:4326')

    def _estimate_road_populations(self) -> NoReturn:
        """
        Use estimates of vehicle occupancy based on vehicle type to estimate the population passing each count point.
        """

        def calc_population(row):
            pop = 0
            for k, v in TYPE_OCCUPANCY.items():
                pop += row[k] * v
            return pop

        self._traffic_counts['population_per_hour'] = self._traffic_counts.apply(calc_population, axis=1) / 24

    def _apply_relative_traffic_variations(self, all_points: List[List[float]]) -> NoReturn:
        """
        Apply the hourly relative variations from the week average for each count point
        """
        # Ingest data, ignoring header and footer info
        relative_variations_df = pd.read_excel(os.sep.join(('static_data', 'tra0307.ods')), engine='odf', header=5,
                                               skipfooter=8)
        # Flatten into continuous list of hourly variations for the week
        relative_variations_flat = (relative_variations_df.iloc[:, 1:] / 100).melt()['value']

        # local_timed_tfc_counts = []
        # # Iterate through the variation for each hourly slot in the week and scale the population/hr with it
        # # TODO: Use Dask to map-reduce this
        # for time_window in relative_variations_flat:
        #     temp = []
        #     for idx, row in self._traffic_counts.iterrows():
        #         temp.append([row.latitude, row.longitude, row.population_per_hour * time_window])
        #     local_timed_tfc_counts.append(temp)

        gv_timed_tfc_counts = None
        all_interp_points = np.array(all_points)
        # Iterate through each hour of the week
        for hour, hour_variation in enumerate(relative_variations_flat):
            temp = all_interp_points[:, 2] * hour_variation  # Scale each pop/hr value by the relative variation
            # Vstack coords back with scaled pop/min values and append as list (for folium)
            stack = np.concatenate((all_interp_points[:, :2], temp[:, None], hour * np.ones(temp.shape)[:, None]),
                                   axis=1)
            if gv_timed_tfc_counts is None:
                gv_timed_tfc_counts = stack
            else:
                gv_timed_tfc_counts = np.concatenate((gv_timed_tfc_counts, stack), axis=0)

        # gv_timed_tfc_counts = []
        # for hour, hour_counts in enumerate(local_timed_interp_tfc_counts):
        #     for lat, lon, val in hour_counts:
        #         gv_timed_tfc_counts.append([lat, lon, val, hour])
        # del local_timed_interp_tfc_counts

        gv_timed_tfc_counts = np.array(gv_timed_tfc_counts)
        gv_timed_tfc_counts_df = pd.DataFrame({'lon': gv_timed_tfc_counts[:, 0], 'lat': gv_timed_tfc_counts[:, 1],
                                               'population': gv_timed_tfc_counts[:, 2],
                                               'hour': gv_timed_tfc_counts[:, 3]})
        dsp.to_parquet(gv_timed_tfc_counts_df, 'timed_tfc.parq.res100', 'lat', 'lon', shuffle='disk', npartitions=32)
        # print(gv_timed_tfc_counts_df.shape)
        # gv_timed_tfc_counts_df.head()

        del gv_timed_tfc_counts
        del gv_timed_tfc_counts_df

    def _ingest_road_geometries(self) -> NoReturn:
        """
        Ingest simplified road geometries in EPSG:27700 coords
        """
        self._roads_geometries = gpd.read_file(os.sep.join(('static_data', '2018-MRDB-minimal.shp'))).set_crs(
            'EPSG:27700').rename(columns={'CP_Number': 'count_point_id'})

    def _interpolate_traffic_counts(self, resolution: int = 50) -> List[List[float]]:
        """
        Interpolate traffic count values between count points along all roads.
        Interpolation points are created at frequency depending on resolution
        :param resolution: The distance in metres between interpolation points along a road
        """
        all_interp_points = []
        proj = Transformer.from_crs(27700, 4326, always_xy=True)
        unique_road_names = self._roads_geometries['RoadNumber'].unique()
        for road_name in unique_road_names:
            # Get the line segments that make up the road
            road_segments = self._roads_geometries[self._roads_geometries['RoadNumber'] == road_name]
            # Get all counts associated with this road
            counts = self._traffic_counts.loc[self._traffic_counts['road_name'] == road_name]
            # Iterate over all road segments
            # Add all road segment coords to flat list of all road coords
            all_segments = []
            flat_proj = [(0, 0)]  # A 1D projection of the road as a line in form (length_coord, value)
            carried_length = 0  # Holder for any carried over road length if a segment is missing a counter
            for _, seg in road_segments.iterrows():
                # Flip the coords around for folium
                coords = np.array(seg['geometry'].coords)[:, [1, 0]]
                all_segments.append(coords)
                # Lookup ID of counter on this segment of road
                pop = counts.loc[counts['count_point_id'] == seg['count_point_id']]['population_per_hour']
                # Check if counter actually exists on this segment
                if pop.size > 0:
                    # If exists append and accumulate this segments length onto
                    #  the 1D projection of this road with the pop/hr value
                    flat_proj.append((seg['geometry'].length + flat_proj[-1][0] + carried_length, pop.item()))
                    carried_length = 0
                else:
                    # If not, carry the length of this segment in the hope the next one will have a counter!
                    carried_length += seg['geometry'].length
            flat_proj = np.array(flat_proj)
            road_ls = so.linemerge(all_segments)  # Stitch the line segments together
            road_length = flat_proj[-1, 0]
            # Generate some intermediate points to interpolate on
            coord_spacing = np.linspace(0, road_length,
                                        int(road_length / resolution))
            # Interpolate linearly on the 1D projection of the road to estimate the interstitial values
            interp_flat_proj = np.interp(coord_spacing, flat_proj[:, 0], flat_proj[:, 1])

            # Recover the true road geometry along with the interpolated values
            for idx, mark in enumerate(coord_spacing):
                c = road_ls.interpolate(mark)
                all_interp_points.append([*proj.transform(c.y, c.x), interp_flat_proj[idx]])

        return all_interp_points
