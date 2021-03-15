import abc
from typing import Tuple

import geopandas as gpd
import numpy as np
import shapely.geometry as sg
from holoviews.element.geom import Geometry
from shapely.geometry import Polygon

from seedpod_ground_risk.layers.layer import Layer


class DataLayer(Layer, abc.ABC):
    """
    Abstract base class for a single layer with its associated data and caches
    """
    key: str
    is_dynamic: bool
    cached_area: Polygon

    def __init__(self, key):
        super().__init__(key)
        self.cached_area = sg.Polygon()

    @abc.abstractmethod
    def generate(self, bounds_polygon: sg.Polygon, raster_shape: Tuple[int, int], from_cache: bool = False, **kwargs) -> Tuple[
        Geometry, np.ndarray, gpd.GeoDataFrame]:
        """
        Generate the map of this layer. This is called asynchronously, so cannot access plot_server members.
        :param raster_shape:
        :param shapely.geometry.Polygon bounds_polygon: the bounding polygon for which to generate the map
        :param bool from_cache: flag to indicate whether to use cached data to fulfill this request
        :return: an Overlay-able holoviews layer with specific options
        """
        pass
