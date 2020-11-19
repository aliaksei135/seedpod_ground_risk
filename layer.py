import abc
from typing import NoReturn

import shapely.geometry as sg
from holoviews.element.geom import Geometry
from shapely.geometry import Polygon


class Layer(abc.ABC):
    """
    Abstract base class for a single layer with its associated data and caches
    """
    key: str
    is_dynamic: bool
    cached_area: Polygon

    def __init__(self, rasterise: bool = True):
        self.key = ''
        self.is_dynamic = False
        self.rasterise = rasterise
        self.cached_area = sg.Polygon()

    @abc.abstractmethod
    def preload_data(self) -> NoReturn:
        """
        Load any data that is expected to remain static for the duration of the program execution.
        This is called when the application is first initialised.
        This method is guaranteed to complete execution before any requests for plot generation to this class.
        """
        pass

    @abc.abstractmethod
    def generate(self, bounds_polygon: sg.Polygon, from_cache: bool = False) -> Geometry:
        """
        Generate the map of this layer. This is called asynchronously, so cannot access plot_server members.
        :param shapely.geometry.Polygon bounds_polygon: the bounding polygon for which to generate the map
        :param bool from_cache: flag to indicate whether to use cached data to fulfill this request
        :return: an Overlay-able holoviews layer with specific options
        """
        pass

    @abc.abstractmethod
    def clear_cache(self) -> NoReturn:
        """
        Clear all cached dynamic data to the state AFTER `preload_data` was called.
        All statically preloaded data should remain intact after calls to this method
        """
        pass
