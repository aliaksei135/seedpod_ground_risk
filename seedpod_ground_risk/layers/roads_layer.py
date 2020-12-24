from typing import NoReturn, List

import geopandas as gpd
import geoviews as gv
import shapely.ops as so
from holoviews.element import Geometry
from shapely import geometry as sg
from shapely import speedups

from seedpod_ground_risk.layer import Layer

gpd.options.use_pygeos = True  # Use GEOS optimised C++ routines
speedups.enable()  # Enable shapely speedups

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
        import datashader.spatial.points as dsp
        import os

        print("Preloading Roads Layer")
        try:
            # self.interpolated_road_populations = spio.read_parquet_dask(
            #     os.sep.join(('static_data', 'timed_tfc.parq')))
            self.interpolated_road_populations = dsp.read_parquet(
                os.sep.join(('static_data', 'timed_tfc.parq')))
        except FileNotFoundError:
            print("Pregenerated roads data not found")
            # Cannot find the pre-generated parquet file, so we have to generate it from scratch
            # Grab some snacks; this takes a while
            # TODO: Prevent low-spec hardware from even attempting to generate the data
            # This takes ~15mins with an i7-7700, 16GiB of RAM with 20GiB of SSD swap for good measure

            print("###########GENERATING NEW ROADS DATA. THIS WILL TAKE A WHILE##############")

            # Ingest and process static traffic counts
            self._ingest_traffic_counts()
            print("Ingested Traffic Count Data")
            self._estimate_road_populations()
            print("Estimated Traffic Populations")
            # Ingest simplified road geometries
            self._ingest_road_geometries()
            print("Ingested Road Geometry Data")
            # Interpolate static traffic counts along road geometries
            all_points = self._interpolate_traffic_counts(resolution=20)
            print("Interpolated Traffic Counts")

            try:
                # Ingest relative weekly variations data and combine with static average traffic counts
                self._apply_relative_traffic_variations(all_points)
                print("Serialised to parquet")
            except Exception as e:
                print(e)

    def generate(self, bounds_polygon: sg.Polygon, from_cache: bool = False, hour: int = 0, **kwargs) -> Geometry:
        from holoviews.operation.datashader import rasterize
        import datashader as ds
        import colorcet
        from time import time

        t0 = time()
        print("Generating Roads Layer Data")

        bounds = bounds_polygon.bounds
        bounded_data = self.interpolated_road_populations[(self.interpolated_road_populations.lat > bounds[0]) &
                                                          (self.interpolated_road_populations.lon > bounds[1]) &
                                                          (self.interpolated_road_populations.lat < bounds[2]) &
                                                          (self.interpolated_road_populations.lon < bounds[3])]
        # bounded_data = self.interpolated_road_populations.cx[bounds[1]:bounds[3], bounds[0]:bounds[2]]
        print("Roads: Bounded data cumtime ", time() - t0)
        points = gv.Points(bounded_data[bounded_data.hour == hour],
                           kdims=['lon', 'lat'], vdims=['population']).opts(colorbar=True, tools=['hover', 'crosshair'],
                                                                            cmap=colorcet.CET_L18, color='population')
        if self.rasterise:
            raster = rasterize(points, aggregator=ds.mean('population'),
                               dynamic=False).opts(colorbar=True, cmap=colorcet.CET_L18, tools=['hover', 'crosshair'])
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
        import pandas as pd
        import os

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
        import spatialpandas as sp
        import spatialpandas.geometry as spg
        import dask.dataframe as dd
        from dask import delayed
        import numpy as np
        import pandas as pd
        import os

        # Ingest data, ignoring header and footer info
        relative_variations_df = pd.read_excel(os.sep.join(('static_data', 'tra0307.ods')), engine='odf',
                                               header=5, skipfooter=8)
        # Flatten into continuous list of hourly variations for the week
        relative_variations_flat = (relative_variations_df.iloc[:, 1:] / 100).melt()['value']

        print("Scaling hourly variations", end='')
        stacks = []
        all_interp_points = np.array(all_points)
        # Iterate through each hour of the week
        for hour, hour_variation in enumerate(relative_variations_flat):
            print(".", hour, end='')
            temp = all_interp_points[:, 2] * hour_variation  # Scale each pop/hr value by the relative variation
            # Vstack coords back with scaled pop/min values and append as list (for folium)
            stack = np.concatenate((all_interp_points[:, :2], temp[:, None], hour * np.ones(temp.shape)[:, None]),
                                   axis=1)
            stacks.append(stack)

        del all_points
        del all_interp_points
        print("Del points")
        gv_timed_tfc_counts_df = delayed(pd.concat([sp.GeoDataFrame(
            {'geometry': spg.PointArray((stack[:, 0], stack[:, 1])),
             'population': stack[:, 2],
             'hour': stack[:, 3]}) for stack in stacks], ignore_index=True))
        del stacks
        # print("Roads dataframe shape ", gv_timed_tfc_counts_df.shape)
        dask_df = dd.from_pandas(gv_timed_tfc_counts_df, npartitions=64)
        del gv_timed_tfc_counts_df
        packed_ddf = dask_df.pack_partitions(npartitions=64)
        del dask_df
        packed_ddf.to_parquet('static_data/timed_tfc.parq')
        # spio.to_parquet(gv_timed_tfc_counts_df, 'static_data/timed_tfc.parq', 'lat', 'lon', shuffle='disk',
        #                 npartitions=32)

    def _ingest_road_geometries(self) -> NoReturn:
        """
        Ingest simplified road geometries in EPSG:27700 coords
        """
        import os

        self._roads_geometries = gpd.read_file(os.sep.join(('static_data', '2018-MRDB-minimal.shp'))).set_crs(
            'EPSG:27700').rename(columns={'CP_Number': 'count_point_id'})

    def _interpolate_traffic_counts(self, resolution: int = 50) -> List[List[float]]:
        """
        Interpolate traffic count values between count points along all roads.
        Interpolation points are created at frequency depending on resolution
        :param resolution: The distance in metres between interpolation points along a road
        """
        import numpy as np
        from pyproj import Transformer

        print("Interpolating road traffic populations along geometries", end='')
        all_interp_points = []
        proj = Transformer.from_crs(27700, 4326, always_xy=True)
        unique_road_names = self._roads_geometries['RoadNumber'].unique()
        for road_name in unique_road_names:
            print(".", end='')
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

        print(".")
        return all_interp_points
