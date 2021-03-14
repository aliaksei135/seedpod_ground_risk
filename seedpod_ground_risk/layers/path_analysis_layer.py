from typing import NoReturn, List, Tuple, Dict

import casex
import geopandas as gpd
import numpy as np
from holoviews.element import Overlay

from seedpod_ground_risk.layers.annotation_layer import AnnotationLayer
from seedpod_ground_risk.pathfinding import bresenham


def get_lethal_area(theta: float, uas_width: float):
    """
    Calculate lethal area of UAS impact from impact angle

    Method from :cite: Smith, P.G. 2000

    :param theta: impact angle in degrees
    :param uas_width: UAS width in metres
    :return:
    """
    r_person = 1  # radius of a person
    h_person = 1.8  # height of a person
    r_uas = uas_width / 2  # UAS halfspan

    return ((2 * (r_person + r_uas) * h_person) / np.tan(np.deg2rad(theta))) + (np.pi * (r_uas + r_person) ** 2)


class PathAnalysisLayer(AnnotationLayer):

    def __init__(self, key: str, filepath: str = '', buffer_dist: float = None, **kwargs):
        super(PathAnalysisLayer, self).__init__(key)
        self.filepath = filepath
        self.buffer_dist = buffer_dist

        import geopandas as gpd
        self.dataframe = gpd.GeoDataFrame()
        self.buffer_poly = None

    def preload_data(self) -> NoReturn:

        self.dataframe = gpd.read_file(self.filepath)
        self.endpoint = self.dataframe.iloc[0].geometry.coords[-1]

    def annotate(self, data: List[gpd.GeoDataFrame], raster_data: Tuple[Dict[str, np.array], np.array],
                 resolution=20, **kwargs) -> Overlay:
        import geoviews as gv
        from scipy.stats import multivariate_normal as mvn

        bounds = (raster_data[0]['Longitude'].min(), raster_data[0]['Latitude'].min(),
                  raster_data[0]['Longitude'].max(), raster_data[0]['Latitude'].max())

        line_coords = list(self.dataframe.iloc[0].geometry.coords)
        # Snap the line string nodes to the raster grid
        snapped_points = [snap_coords_to_grid(raster_data[0], *coords) for coords in line_coords]
        # Generate pairs of consecutive (x,y) coords
        path_pairs = list(map(list, zip(snapped_points, snapped_points[1:])))
        headings = []
        for i in range(1, len(line_coords)):
            prev = line_coords[i - 1]
            next = line_coords[i]
            x = np.sin(next[0] - prev[0]) * np.cos(next[1])
            y = np.cos(prev[1]) * np.sin(next[1]) - np.sin(prev[1]) * np.cos(next[1]) * np.cos(next[0] - prev[0])
            angle = np.arctan2(x, y) % 2 * np.pi
            headings.append(angle)
        # Feed these pairs into the Bresenham algo to find the intermediate points
        path_grid_points = [bresenham.make_line(*pair[0], *pair[1]) for pair in path_pairs]
        # Bring all these points together and remove duplicate coords
        # Flip left to right as bresenham spits out in (y,x) order
        path_grid_points = np.unique(np.concatenate(path_grid_points, axis=0), axis=0)

        ca_model = casex.CriticalAreaModels()  # Lethal area model using default params for human dimensions
        aircraft = casex.AircraftSpecs(casex.enums.AircraftType.FIXED_WING, 2, 2, 2)  # Default aircraft
        aircraft.set_ballistic_drag_coefficient(0.8)
        aircraft.set_ballistic_frontal_area(3)
        fc = casex.FrictionCoefficients()
        aircraft.set_friction_coefficient(
            fc.get_coefficient(casex.enums.AircraftMaterial.ALUMINUM, casex.enums.GroundMaterial.CONCRETE))
        ballistic_model = casex.BallisticDescent2ndOrderDragApproximation()
        ballistic_model.set_aircraft(aircraft)
        distance_impact, velocity_impact, angle_impact, time_impact = ballistic_model.compute_ballistic_distance(
            133, 20, 1)
        ca_model.critical_area(casex.enums.CriticalAreaModel.JARUS,
                               aircraft, velocity_impact,
                               angle_impact, 0)

        # Testing fixed pdf for now
        dist_mean = np.array([-5, 5])

        # Create grid on which to evaluate each point of path with its pdf
        raster_shape = raster_data[1].shape
        x, y = np.mgrid[0:raster_shape[0], 0:raster_shape[1]]
        eval_grid = np.dstack((x, y))

        from pathos.multiprocessing import Pool
        from pathos.multiprocessing import cpu_count
        pool = Pool()

        # TODO Use something like Dask or OpenCV to speed this up in future as it's a simple map-reduce
        def point_dist(c):
            pdf_mean = c + dist_mean
            return mvn(pdf_mean, [[15, 5], [5, 7]]).pdf(eval_grid)

        def map_chunk(coords):
            return np.sum([point_dist(c) for c in coords], axis=0)

        # TODO Remove all these flip and rotates; the indices must be swapping somewhere else?
        pdfs = pool.map(map_chunk, np.array_split(path_grid_points, cpu_count() * 2))
        pool.close()
        pdf_mat = np.sum(pdfs, axis=0)

        a_exp = self.get_lethal_area(30)
        # Probability * Pop. Density * Lethal Area
        risk_map = pdf_mat * raster_data[1] * a_exp

        risk_raster = gv.Image(risk_map, bounds=bounds).options(alpha=0.7, cmap='viridis', tools=['hover'],
                                                                clipping_colors={'min': (0, 0, 0, 0)})
        risk_raster = risk_raster.redim.range(z=(1e-11, risk_map.max()))

        # labels = []
        # annotation_layers = []
        # for gdf in data:
        #     if not gdf.crs:
        #         # If CRS is not set, set EPSG4326 without reprojection as it must be EPSG4326 to display properly
        #         gdf.set_crs(epsg=4326, inplace=True)
        #     overlay = gpd.overlay(gdf, self.buffer_poly, how='intersection')
        #
        #     geom_type = overlay.geometry.geom_type.all()
        #     if geom_type == 'Polygon' or geom_type == 'MultiPolygon':
        #         if 'density' not in gdf:
        #             continue
        #         proj_gdf = overlay.to_crs('epsg:27700')
        #         proj_gdf['population'] = proj_gdf.geometry.area * proj_gdf.density
        #         labels.append(gv.Text(self.endpoint[0], self.endpoint[1],
        #                               f"Static Population: {proj_gdf['population'].sum():.2f}", fontsize=20).opts(
        #             style={'color': 'blue'}))
        #         proj_gdf = proj_gdf.to_crs('EPSG:4326')
        #         annotation_layers.append(
        #             gv.Polygons(proj_gdf, vdims=['population']).opts(alpha=0.8, color='cyan', tools=['hover']))
        #     elif geom_type == 'Point':
        #         if 'population' in overlay:
        #             # Group data by road name, localising the points
        #             road_geoms = list(overlay.groupby('road_name').geometry)
        #             road_coms = {}  # store the centre of mass of points associated with a road
        #             for name, geoms in road_geoms:
        #                 mean_lon = sum([p.x for p in geoms]) / len(geoms)
        #                 mean_lat = sum([p.y for p in geoms]) / len(geoms)
        #                 road_coms[name] = (mean_lon, mean_lat)  # x,y order
        #             # get mean population flow of points for road
        #             road_pops = list(overlay.groupby('road_name').mean().itertuples())
        #             for name, pop, *_ in road_pops:  # add labels at the centre of mass of each group of points
        #                 labels.append(gv.Text(road_coms[name][0], road_coms[name][1],
        #                                       f'Population flow on road {name}: {pop * 60:.2f}/min',
        #                                       fontsize=20).opts(
        #                     style={'color': 'blue'}))
        #         annotation_layers.append((gv.Points(overlay).opts(style={'alpha': 0.8, 'color': 'cyan'})))
        #     elif geom_type == 'Line':
        #         pass

        return Overlay([
            gv.Contours(self.dataframe).opts(line_width=4, line_color='magenta'),
            # gv.Polygons(self.buffer_poly).opts(style={'alpha': 0.3, 'color': 'cyan'}),
            # Add the path stats as a text annotation to the final path point
            # *labels,
            # *annotation_layers,
            risk_raster
        ])

    def clear_cache(self) -> NoReturn:
        pass

    def _snap_coords_to_grid(self, grid, lon: float, lat: float) -> Tuple[int, int]:
        """
        Snap coordinates to grid indices
        :param grid: raster grid coordinates
        :param lon: longitude to snap
        :param lat: latitude to snap
        :return: (x, y) tuple of grid indices
        """
        lat_idx = int(np.argmin(np.abs(grid['Latitude'] - lat)))
        lon_idx = int(np.argmin(np.abs(grid['Longitude'] - lon)))

        return lon_idx, lat_idx

    def get_lethal_area(self, theta: float):
        """
        Calculate lethal area of UAS impact from impact angle

        Method from Smith, P.G. 2000

        :param theta: impact angle in degrees
        :return:
        """
        r_person = 1  # radius of a person
        h_person = 1.8  # height of a person

        r_uas = 0.5  # UAS radius/halfspan

        return ((2 * (r_person + r_uas) * h_person) / np.tan(np.deg2rad(theta))) + (np.pi * (r_uas + r_person) ** 2)
