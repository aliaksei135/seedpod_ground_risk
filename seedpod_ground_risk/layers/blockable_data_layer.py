import random
from abc import ABCMeta, abstractmethod

from seedpod_ground_risk.layers.data_layer import DataLayer


class BlockableDataLayer(DataLayer, metaclass=ABCMeta):
    def __init__(self, key, colour: str = None,
                 blocking=False, buffer_dist=0):
        super().__init__(key)
        self.blocking = blocking
        self.buffer_dist = buffer_dist
        # Set a random colour
        self._colour = colour if colour is not None else "#" + ''.join(
            [random.choice('0123456789ABCDEF') for _ in range(6)])

    @abstractmethod
    def preload_data(self):
        pass

    @abstractmethod
    def generate(self, bounds_polygon, raster_shape, from_cache: bool = False, **kwargs):
        pass

    @abstractmethod
    def clear_cache(self):
        pass
