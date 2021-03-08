from typing import NoReturn, List, Tuple, Dict

import geopandas as gpd
import numpy as np
from holoviews.element import Overlay

from seedpod_ground_risk.layers.annotation_layer import AnnotationLayer
from seedpod_ground_risk.pathfinding import bresenham


class GeoJSONLayer(AnnotationLayer):

    def __init__(self, key: str, filepath: str = '', buffer_dist: float = None, **kwargs):
        super(GeoJSONLayer, self).__init__(key)
        self.filepath = filepath
        self.buffer_dist = buffer_dist

        import geopandas as gpd
        self.dataframe = gpd.GeoDataFrame()
        self.buffer_poly = None

    def preload_data(self) -> NoReturn:

        self.dataframe = gpd.read_file(self.filepath)
        if self.buffer_dist:
            epsg27700_geom = self.dataframe.to_crs('EPSG:27700').geometry
            self.buffer_poly = gpd.GeoDataFrame(
                {'geometry': epsg27700_geom.buffer(self.buffer_dist).to_crs('EPSG:4326')}
            )
        self.endpoint = self.dataframe.iloc[0].geometry.coords[-1]

    def annotate(self, data: List[gpd.GeoDataFrame], raster_data: Tuple[Dict[str, np.array], np.array],
                 **kwargs) -> Overlay:
        import geoviews as gv
        from scipy.stats import multivariate_normal as mvn

        bounds = (raster_data[0]['Longitude'].min(), raster_data[0]['Latitude'].min(),
                  raster_data[0]['Longitude'].max(), raster_data[0]['Latitude'].max())

        if self.buffer_poly is not None:
            # Snap the line string nodes to the raster grid
            snapped_points = [self._snap_coords_to_grid(raster_data[0], *coords) for coords in
                              self.dataframe.iloc[0].geometry.coords]
            # Generate pairs of consecutive (x,y) coords
            path_pairs = list(map(list, zip(snapped_points, snapped_points[1:])))
            # Feed these pairs into the Bresenham algo to find the intermediate points
            path_grid_points = [bresenham.make_line(*pair[0], *pair[1]) for pair in path_pairs]
            # Bring all these points together and remove duplicate coords
            # Flip left to right as bresenham spits out in (y,x) order
            path_grid_points = np.fliplr(np.unique(np.concatenate(path_grid_points, axis=0), axis=0))

            dist_mean = np.array([5, 5])
            raster_shape = raster_data[1].shape
            x, y = np.mgrid[0:raster_shape[0], 0:raster_shape[1]]
            eval_grid = np.dstack((x, y))

            def point_dist(c):
                pdf_mean = c + dist_mean
                return mvn(pdf_mean, [[10, 0], [0, 10]]).pdf(eval_grid)

            # TODO Remove all these flip and rotates; the indices must be swapping somewhere else?
            pdf_mat = np.rot90(np.sum([point_dist(c) for c in path_grid_points], axis=0))

            labels = []
            annotation_layers = []
            for gdf in data:
                if not gdf.crs:
                    # If CRS is not set, set EPSG4326 without reprojection as it must be EPSG4326 to display properly
                    gdf.set_crs(epsg=4326, inplace=True)
                overlay = gpd.overlay(gdf, self.buffer_poly, how='intersection')

                geom_type = overlay.geometry.geom_type.all()
                if geom_type == 'Polygon' or geom_type == 'MultiPolygon':
                    if 'density' not in gdf:
                        continue
                    proj_gdf = overlay.to_crs('epsg:27700')
                    proj_gdf['population'] = proj_gdf.geometry.area * proj_gdf.density
                    labels.append(gv.Text(self.endpoint[0], self.endpoint[1],
                                          f"Static Population: {proj_gdf['population'].sum():.2f}", fontsize=20).opts(
                        style={'color': 'blue'}))
                    proj_gdf = proj_gdf.to_crs('EPSG:4326')
                    annotation_layers.append(
                        gv.Polygons(proj_gdf, vdims=['population']).opts(alpha=0.8, color='cyan', tools=['hover']))
                elif geom_type == 'Point':
                    if 'population' in overlay:
                        # Group data by road name, localising the points
                        road_geoms = list(overlay.groupby('road_name').geometry)
                        road_coms = {}  # store the centre of mass of points associated with a road
                        for name, geoms in road_geoms:
                            mean_lon = sum([p.x for p in geoms]) / len(geoms)
                            mean_lat = sum([p.y for p in geoms]) / len(geoms)
                            road_coms[name] = (mean_lon, mean_lat)  # x,y order
                        # get mean population flow of points for road
                        road_pops = list(overlay.groupby('road_name').mean().itertuples())
                        for name, pop in road_pops:  # add labels at the centre of mass of each group of points
                            labels.append(gv.Text(road_coms[name][0], road_coms[name][1],
                                                  f'Population flow on road {name}: {pop / 60:.2f}/min',
                                                  fontsize=20).opts(
                                style={'color': 'blue'}))
                    annotation_layers.append((gv.Points(overlay).opts(style={'alpha': 0.8, 'color': 'cyan'})))
                elif geom_type == 'Line':
                    pass

            return Overlay([
                gv.Contours(self.dataframe).opts(line_width=4, line_color='magenta'),
                gv.Polygons(self.buffer_poly).opts(style={'alpha': 0.3, 'color': 'cyan'}),
                # Add the path stats as a text annotation to the final path point
                *labels,
                *annotation_layers
            ])
        else:
            return gv.Contours(self.dataframe).opts(line_width=4, line_color='#000000')

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
