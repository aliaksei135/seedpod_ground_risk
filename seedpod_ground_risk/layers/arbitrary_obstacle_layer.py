from typing import NoReturn, Tuple

import geopandas as gpd
import numpy as np
from holoviews.element import Geometry
from shapely import geometry as sg

from seedpod_ground_risk.layers.blockable_data_layer import BlockableDataLayer


class ArbitraryObstacleLayer(BlockableDataLayer):
    def __init__(self, key, filepath: str = '', **kwargs):
        super(ArbitraryObstacleLayer, self).__init__(key, **kwargs)
        self.filepath = filepath

    def preload_data(self) -> NoReturn:

        self.dataframe = gpd.read_file(self.filepath)
        if self.buffer_dist:
            epsg3857_geom = self.dataframe.to_crs('EPSG:3857').geometry
            self.buffer_poly = gpd.GeoDataFrame(
                {'geometry': epsg3857_geom.buffer(self.buffer_dist).to_crs('EPSG:4326')}
            )

    def generate(self, bounds_polygon: sg.Polygon, raster_shape: Tuple[int, int], from_cache: bool = False, **kwargs) -> \
            Tuple[Geometry, np.ndarray, gpd.GeoDataFrame]:
        import geoviews as gv
        from holoviews.operation.datashader import rasterize

        bounds = bounds_polygon.bounds

        bounded_df = self.dataframe.cx[bounds[1]:bounds[3], bounds[0]:bounds[2]]

        polys = gv.Polygons(bounded_df).opts(style={'alpha': 0.8, 'color': self._colour})
        raster = rasterize(polys, width=raster_shape[0], height=raster_shape[1],
                           x_range=(bounds[1], bounds[3]), y_range=(bounds[0], bounds[2]), dynamic=False)
        raster_grid = np.copy(list(raster.data.data_vars.items())[0][1].data.astype(np.float))
        if self.blocking:
            raster_grid[raster_grid != 0] = -1

        return polys, raster_grid, gpd.GeoDataFrame(self.dataframe)

    def clear_cache(self):
        pass
