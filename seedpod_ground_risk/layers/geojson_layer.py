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
            label_str = ''

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
                    label_str += f"Static Population: {proj_gdf['population'].sum():.2f}"
                    annotation_layers.append(gv.Polygons(overlay).opts(style={'alpha': 0.8, 'color': 'cyan'}))
                elif geom_type == 'Point':
                    if 'population' in overlay:
                        mean_pop = overlay.population.mean()
                        label_str += f'Dynamic Population: {mean_pop / 60:.2f}/min'
                    annotation_layers.append((gv.Points(overlay).opts(style={'alpha': 0.8, 'color': 'cyan'})))
                elif geom_type == 'Line':
                    pass

                label_str += '\n'

            return Overlay([
                gv.Contours(self.dataframe).opts(line_width=4, line_color='magenta'),
                gv.Polygons(self.buffer_poly).opts(style={'alpha': 0.3, 'color': 'cyan'}),
                # Add the path stats as a text annotation to the final path point
                gv.Text(self.endpoint[0], self.endpoint[1], label_str, fontsize=20).opts(style={'color': 'blue'}),
                *annotation_layers
            ])
        else:
            return gv.Contours(self.dataframe).opts(line_width=4, line_color='#000000')

    def clear_cache(self) -> NoReturn:
        pass
