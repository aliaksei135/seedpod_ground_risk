from typing import NoReturn, List

import geopandas as gpd
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
            self.buffer_poly = epsg27700_geom.buffer(self.buffer_dist).to_crs('EPSG:4326')

    def annotate(self, data: List[gpd.GeoDataFrame], **kwargs) -> Geometry:
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
