from typing import NoReturn, List, Tuple, Dict

import geopandas as gpd
import numpy as np
from holoviews.element import Overlay

from seedpod_ground_risk.layers.annotation_layer import AnnotationLayer


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

        if self.buffer_poly is not None:
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
                    annotation_layers.append(gv.Polygons(overlay).opts(style={'alpha': 0.8, 'color': 'cyan'}))
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
