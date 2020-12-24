from typing import NoReturn

from holoviews.element import Geometry
from shapely import geometry as sg

from seedpod_ground_risk.layer import Layer


class GeoJSONLayer(Layer):

    def __init__(self, geojson_filepath, **kwargs):
        import os

        key = os.path.basename(geojson_filepath)
        super(GeoJSONLayer, self).__init__(key, **kwargs)
        self.filepath = geojson_filepath

        import geopandas as gpd
        self.dataframe = gpd.GeoDataFrame()

    def preload_data(self) -> NoReturn:
        import geopandas as gpd

        self.dataframe = gpd.read_file(self.filepath)

    def generate(self, bounds_polygon: sg.Polygon, from_cache: bool = False, **kwargs) -> Geometry:
        import geoviews as gv

        return gv.Contours(self.dataframe).opts(line_width=5)

    def clear_cache(self) -> NoReturn:
        pass
