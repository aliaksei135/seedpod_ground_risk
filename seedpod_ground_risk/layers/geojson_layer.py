from typing import NoReturn

from holoviews.element import Geometry, Overlay
from shapely import geometry as sg

from seedpod_ground_risk.layer import Layer


class GeoJSONLayer(Layer):

    def __init__(self, geojson_filepath, buffer: float = None, **kwargs):
        import os

        key = os.path.basename(geojson_filepath)
        super(GeoJSONLayer, self).__init__(key, **kwargs)
        self.filepath = geojson_filepath
        self.buffer_dist = buffer

        import geopandas as gpd
        self.dataframe = gpd.GeoDataFrame()
        self.buffer_poly = None

    def preload_data(self) -> NoReturn:
        import geopandas as gpd

        self.dataframe = gpd.read_file(self.filepath)
        if self.buffer_dist:
            epsg27700_geom = self.dataframe.to_crs('EPSG:27700').geometry
            self.buffer_poly = epsg27700_geom.buffer(self.buffer_dist).to_crs('EPSG:4326')

    def generate(self, bounds_polygon: sg.Polygon, from_cache: bool = False, **kwargs) -> Geometry:
        import geoviews as gv

        if self.buffer_poly is not None:
            return Overlay([
                gv.Contours(self.dataframe).opts(line_width=4, line_color='#000000'),
                gv.Polygons(self.buffer_poly[0]).opts(style={'alpha': 0.4})
            ])
        else:
            return gv.Contours(self.dataframe).opts(line_width=4, line_color='#000000')

    def clear_cache(self) -> NoReturn:
        pass
