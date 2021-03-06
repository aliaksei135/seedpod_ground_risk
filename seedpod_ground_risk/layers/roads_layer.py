from typing import NoReturn, List, Tuple

import geopandas as gpd
import numpy as np
from holoviews.element import Geometry
from shapely import geometry as sg
from shapely import speedups

from seedpod_ground_risk.layers.data_layer import DataLayer

gpd.options.use_pygeos = True  # Use GEOS optimised C++ routines
speedups.enable()  # Enable shapely speedups

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
HOURS_OF_DAY = range(24)

TRAFFIC_COUNT_COLUMNS = ['count_point_id', 'year', 'latitude', 'longitude', 'road_name', 'pedal_cycles',
                         'two_wheeled_motor_vehicles', 'cars_and_taxis', 'buses_and_coaches',
                         'lgvs', 'all_hgvs', 'all_motor_vehicles']

# https://www.gov.uk/government/statistical-data-sets/nts09-vehicle-mileage-and-occupancy#carvan-occupancy
# other types plausibly estimated.
TYPE_OCCUPANCY = {
    'pedal_cycles': 1,
    'two_wheeled_motor_vehicles': 1.4,
    'cars_and_taxis': 1.6,
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


class RoadsLayer(DataLayer):
    _traffic_counts: gpd.GeoDataFrame

    def __init__(self, key, **kwargs):
        from pyproj import Transformer

        super(RoadsLayer, self).__init__(key)

        self.proj = Transformer.from_crs(27700, 4326, always_xy=True)
        self.reverse_proj = Transformer.from_crs(4326, 27700, always_xy=True)

        self.week_timesteps = generate_week_timesteps()

        self._traffic_counts = gpd.GeoDataFrame()  # Traffic counts in EPSG:4326 coords
        self._roads_geometries = gpd.GeoDataFrame()  # Road Geometries in EPSG:27700 coords
        self.relative_variations_flat = gpd.GeoDataFrame()  # Relative traffic variations

    def preload_data(self) -> NoReturn:

        print("Preloading Roads Layer")
        self._ingest_traffic_counts()
        self._estimate_road_populations()
        self._ingest_road_geometries()
        self._ingest_relative_traffic_variations()

    def generate(self, bounds_polygon: sg.Polygon, raster_shape: Tuple[int, int], from_cache: bool = False,
                 hour: int = 0, **kwargs) -> \
            Tuple[Geometry, np.ndarray, gpd.GeoDataFrame]:
        from holoviews.operation.datashader import rasterize
        import geoviews as gv
        import datashader as ds
        import colorcet

        relative_variation = self.relative_variations_flat[hour]

        road_points = self._interpolate_traffic_counts(bounds_polygon)
        points = np.array(road_points)[:, :3].astype(np.float)
        names = np.array(road_points)[:, 3]
        tfc_df = gpd.GeoDataFrame(
            {'geometry': [sg.Point(lon, lat) for lon, lat in zip(points[:, 0], points[:, 1])],
             'population': points[:, 2] * relative_variation,
             'road_name': names})
        points = gv.Points(tfc_df,
                           kdims=['Longitude', 'Latitude'], vdims=['population']).opts(colorbar=True,
                                                                                       cmap=colorcet.CET_L18,
                                                                                       color='population')
        bounds = bounds_polygon.bounds
        raster = rasterize(points, aggregator=ds.mean('population'), width=raster_shape[0], height=raster_shape[1],
                           x_range=(bounds[1], bounds[3]), y_range=(bounds[0], bounds[2]), dynamic=False)
        raster_grid = np.copy(list(raster.data.data_vars.items())[0][1].data.astype(np.float))
        return points, raster_grid, gpd.GeoDataFrame(tfc_df)

    def clear_cache(self) -> NoReturn:
        self._traffic_counts = gpd.GeoDataFrame()
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

    def _ingest_relative_traffic_variations(self):
        import pandas as pd
        import os

        # Ingest data, ignoring header and footer info
        relative_variations_df = pd.read_excel(os.sep.join(('static_data', 'tra0307.ods')), engine='odf',
                                               header=5, skipfooter=8)
        # Flatten into continuous list of hourly variations for the week
        self.relative_variations_flat = (relative_variations_df.iloc[:, 1:] / 100).melt()['value']

    def _ingest_road_geometries(self) -> NoReturn:
        """
        Ingest simplified road geometries in EPSG:27700 coords
        """
        import os

        self._roads_geometries = gpd.read_file(os.sep.join(('static_data', '2018-MRDB-minimal.shp'))).rename(
            columns={'CP_Number': 'count_point_id'})
        if not self._roads_geometries.crs:
            self._roads_geometries = self._roads_geometries.set_crs('EPSG:27700')

    def _interpolate_traffic_counts(self, bounds_poly: sg.Polygon, resolution: int = 20) -> List[
        List[float]]:
        """
        Interpolate traffic count values between count points along all roads.
        Interpolation points are created at frequency depending on resolution
        :param bounds_poly: Bounding polygon for roads to interpolate
        :param resolution: The distance in metres between interpolation points along a road
        """
        import numpy as np
        import shapely.ops as so

        b = bounds_poly.bounds
        bounds = [0] * 4
        bounds[0], bounds[1] = self.reverse_proj.transform(b[1], b[0])
        bounds[2], bounds[3] = self.reverse_proj.transform(b[3], b[2])
        unique_road_names = self._roads_geometries.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]['RoadNumber'].unique()

        all_interp_points = []
        all_interp_points_append = all_interp_points.append
        for road_name in unique_road_names:
            print(".", end='')
            # Get the line segments that make up the road
            road_segments = self._roads_geometries[self._roads_geometries['RoadNumber'] == road_name].cx[
                            bounds[0]:bounds[2], bounds[1]:bounds[3]]
            # Get all counts associated with this road
            counts = self._traffic_counts.loc[self._traffic_counts['road_name'] == road_name]
            # Iterate over all road segments
            # Add all road segment coords to flat list of all road coords
            all_segments = []
            all_segments_append = all_segments.append

            flat_proj = [(0, 0)]  # A 1D projection of the road as a line in form (length_coord, value)
            flat_proj_append = flat_proj.append
            carried_length = 0  # Holder for any carried over road length if a segment is missing a counter
            for _, seg in road_segments.iterrows():
                # Flip the coords around for folium
                coords = np.array(seg['geometry'].coords)[:, [1, 0]]
                all_segments_append(coords)
                # Lookup ID of counter on this segment of road
                pop = counts.loc[counts['count_point_id'] == seg['count_point_id']]['population_per_hour']
                # Check if counter actually exists on this segment
                if pop.size > 0:
                    # If exists append and accumulate this segments length onto
                    #  the 1D projection of this road with the pop/hr value
                    flat_proj_append((seg['geometry'].length + flat_proj[-1][0] + carried_length, pop.item()))
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
                all_interp_points_append([*self.proj.transform(c.y, c.x), interp_flat_proj[idx], road_name])

        print(".")
        return all_interp_points
