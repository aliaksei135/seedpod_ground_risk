from typing import NoReturn, List, Tuple, Dict

import geopandas as gpd
import numpy as np
from holoviews.element import Geometry, Overlay

from seedpod_ground_risk.layers.annotation_layer import AnnotationLayer


class GeoJSONLayer(AnnotationLayer):

    def __init__(self, key: str, geojson_filepath: str, buffer: float = None, **kwargs):
        super(GeoJSONLayer, self).__init__(key, **kwargs)
        self.filepath = geojson_filepath
        self.buffer_dist = buffer

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

    def annotate(self, data: List[gpd.GeoDataFrame], raster_data: Tuple[Dict[str, np.array], np.array],
                 **kwargs) -> Geometry:
        import geoviews as gv

        if self.buffer_poly is not None:
            annotation_layers = []
            for gdf in data:
                if not gdf.crs:
                    # If CRS is not set, set EPSG4326 without reprojection as it must be EPSG4326 to display properly
                    gdf.set_crs(epsg=4326, inplace=True)
                overlay = gpd.overlay(gdf, self.buffer_poly, how='intersection')

                geom_type = overlay.geometry.geom_type.all()
                if geom_type == 'Polygon':
                    if 'density' not in gdf:
                        continue
                    proj_gdf = overlay.to_crs('epsg:27700')
                    proj_gdf['population'] = proj_gdf.geometry.area * proj_gdf.density
                    print("Geometry Swept Population: ", proj_gdf['population'].sum())
                    annotation_layers.append(gv.Polygons(overlay).opts(style={'alpha': 0.8, 'color': 'cyan'}))
                elif geom_type == 'Point':
                    if 'population' in overlay:
                        mean_pop = overlay.population.mean()
                        print("Points mean ", mean_pop)
                    annotation_layers.append((gv.Points(overlay).opts(style={'alpha': 0.8, 'color': 'cyan'})))
                elif geom_type == 'Line':
                    pass

            return Overlay([
                gv.Contours(self.dataframe).opts(line_width=4, line_color='magenta'),
                gv.Polygons(self.buffer_poly).opts(style={'alpha': 0.3, 'color': 'cyan'}),
                *annotation_layers
            ])
        else:
            return gv.Contours(self.dataframe).opts(line_width=4, line_color='#000000')

    def clear_cache(self) -> NoReturn:
        pass
