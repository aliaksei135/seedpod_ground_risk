from typing import NoReturn, Tuple

import geopandas as gpd
import numpy as np
from holoviews.element import Geometry
from shapely import geometry as sg
from shapely import speedups

from seedpod_ground_risk.data.external_data_references import traffic_count_filepath, road_geometry_filepath, \
    relative_variation_filepath
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


# https://gis.stackexchange.com/questions/291247/interchange-y-x-to-x-y-with-geopandas-python-or-qgis
def swap_xy(geom):
    if geom.is_empty:
        return geom

    if geom.has_z:
        def swap_xy_coords(coords):
            for x, y, z in coords:
                yield (y, x, z)
    else:
        def swap_xy_coords(coords):
            for x, y in coords:
                yield (y, x)

    # Process coordinates from each supported geometry type
    if geom.type in ('Point', 'LineString', 'LinearRing'):
        return type(geom)(list(swap_xy_coords(geom.coords)))
    elif geom.type == 'Polygon':
        ring = geom.exterior
        shell = type(ring)(list(swap_xy_coords(ring.coords)))
        holes = list(geom.interiors)
        for pos, ring in enumerate(holes):
            holes[pos] = type(ring)(list(swap_xy_coords(ring.coords)))
        return type(geom)(shell, holes)
    elif geom.type.startswith('Multi') or geom.type == 'GeometryCollection':
        # Recursive call
        return type(geom)([swap_xy(part) for part in geom.geoms])
    else:
        raise ValueError('Type %r not recognized' % geom.type)


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
                 hour: int = 8, resolution: float = 20, **kwargs) -> \
            Tuple[Geometry, np.ndarray, gpd.GeoDataFrame]:
        from holoviews.operation.datashader import rasterize
        import geoviews as gv
        import datashader as ds
        import colorcet

        relative_variation = self.relative_variations_flat[hour]

        roads_gdf = self._interpolate_traffic_counts(bounds_polygon)
        roads_gdf['population_per_hour'] = roads_gdf['population_per_hour'] * relative_variation
        roads_gdf['population'] = roads_gdf['population_per_hour'] / 3600
        roads_gdf['density'] = roads_gdf['population'] / (roads_gdf.geometry.area * 1e-6)  # km^2
        ln_mask = roads_gdf['density'] > 0
        roads_gdf.loc[ln_mask, 'ln_density'] = np.log(roads_gdf.loc[ln_mask, 'density'])
        roads_gdf['ln_density'].fillna(0, inplace=True)
        roads_gdf = roads_gdf.set_crs('EPSG:27700').to_crs('EPSG:4326')

        points = gv.Polygons(roads_gdf,
                             kdims=['Longitude', 'Latitude'],
                             vdims=['population_per_hour', 'ln_density', 'density']).opts(
            # colorbar=True,
            cmap=colorcet.CET_L18,
            color='ln_density',
            line_color='ln_density')
        bounds = bounds_polygon.bounds
        raster = rasterize(points, aggregator=ds.mean('density'), width=raster_shape[0], height=raster_shape[1],
                           x_range=(bounds[1], bounds[3]), y_range=(bounds[0], bounds[2]), dynamic=False)
        raster_grid = np.copy(list(raster.data.data_vars.items())[0][1].data.astype(np.float))
        return points, raster_grid, gpd.GeoDataFrame(roads_gdf)

    def clear_cache(self) -> NoReturn:
        self._traffic_counts = gpd.GeoDataFrame()
        self._roads_geometries = gpd.GeoDataFrame()

    def _ingest_traffic_counts(self) -> NoReturn:
        """
        Ingest annualised average daily flow traffic counts
        Only the latest year of data is used.
        """
        import pandas as pd

        # Ingest raw data
        traffic_filepath = traffic_count_filepath()
        counts_df = pd.read_csv(traffic_filepath)
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

        # Ingest data, ignoring header and footer info
        rel_var_filepath = relative_variation_filepath()
        relative_variations_df = pd.read_excel(rel_var_filepath, engine='odf',
                                               header=5, skipfooter=8)
        # Flatten into continuous list of hourly variations for the week
        self.relative_variations_flat = (relative_variations_df.iloc[:, 1:] / 100).melt()['value']

    def _ingest_road_geometries(self) -> NoReturn:
        """
        Ingest simplified road geometries in EPSG:27700 coords
        """
        road_geom_filepath = road_geometry_filepath()
        self._roads_geometries = gpd.read_file(road_geom_filepath).rename(columns={'CP_Number': 'count_point_id'})
        if not self._roads_geometries.crs:
            self._roads_geometries = self._roads_geometries.set_crs('EPSG:27700')

    def _interpolate_traffic_counts(self, bounds_poly: sg.Polygon, resolution: int = 20) -> gpd.GeoDataFrame:
        """
        Interpolate traffic count values between count points along all roads.
        Interpolation points are created at frequency depending on resolution
        :param bounds_poly: Bounding polygon for roads to interpolate
        :param resolution: The distance in metres between interpolation points along a road
        """
        import numpy as np
        import shapely.ops as so
        import pandas as pd

        b = bounds_poly.bounds
        bounds = [0] * 4
        bounds[0], bounds[1] = self.reverse_proj.transform(b[1], b[0])
        bounds[2], bounds[3] = self.reverse_proj.transform(b[3], b[2])
        unique_road_names = self._roads_geometries.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]['RoadNumber'].unique()

        all_road_gdfs = []
        for road_name in unique_road_names:
            if road_name.startswith('M'):
                road_width = 22
            else:
                road_width = 14.6
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
            road_ls = swap_xy(so.linemerge(all_segments))  # Stitch the line segments together
            road_width_buffer_gdf = gpd.GeoDataFrame(geometry=[road_ls.buffer(road_width)])
            road_length = flat_proj[-1, 0]
            # Generate some intermediate points to interpolate on
            coord_spacing = np.linspace(0, road_length,
                                        int(road_length / resolution))
            # Interpolate linearly on the 1D projection of the road to estimate the interstitial values
            interp_flat_proj = np.interp(coord_spacing, flat_proj[:, 0], flat_proj[:, 1])

            point_polys = []
            pops = []
            # Recover the true road geometry along with the interpolated values
            for idx, mark in enumerate(coord_spacing):
                c = road_ls.interpolate(mark)
                point_poly = c.buffer(resolution / 2, cap_style=sg.CAP_STYLE.square)
                point_polys.append(point_poly)
                pops.append(interp_flat_proj[idx])

            road_gdf = gpd.GeoDataFrame(
                {'geometry': point_polys, 'population_per_hour': pops, 'road_name': len(pops) * [road_name]})
            if not road_gdf.empty:
                road_gdf = gpd.overlay(road_gdf, road_width_buffer_gdf, how='intersection')
                all_road_gdfs.append(road_gdf)

        roads_gdf = pd.concat(all_road_gdfs)
        return roads_gdf
