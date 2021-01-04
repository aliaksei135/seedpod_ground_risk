import abc

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

    def __init__(self, key, rasterise: bool = True):
        self.key = key
        self.is_dynamic = False
        self.rasterise = rasterise
        self.cached_area = sg.Polygon()

    @abc.abstractmethod
    def generate(self, bounds_polygon: sg.Polygon, from_cache: bool = False, **kwargs) -> Geometry:
        """
        Generate the map of this layer. This is called asynchronously, so cannot access plot_server members.
        :param shapely.geometry.Polygon bounds_polygon: the bounding polygon for which to generate the map
        :param bool from_cache: flag to indicate whether to use cached data to fulfill this request
        :return: an Overlay-able holoviews layer with specific options
        """
        pass

