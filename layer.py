import abc

import shapely.geometry as sg
from holoviews.element.geom import Geometry


class Layer(abc.ABC):

    def __init__(self):
        self.key = ''
        self.is_dynamic = False
        self.cached_area = sg.Polygon()

    @abc.abstractmethod
    def preload_data(self):
        pass

    @abc.abstractmethod
    def generate(self, bounds_polygon: sg.Polygon, from_cache: bool = False) -> Geometry:
        pass

    @abc.abstractmethod
    def clear_cache(self):
        pass
