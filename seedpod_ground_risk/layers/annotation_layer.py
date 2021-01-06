import abc
from typing import List

import geopandas as gpd
import numpy as np
from holoviews.element.geom import Geometry

from seedpod_ground_risk.layers.layer import Layer


class AnnotationLayer(Layer, abc.ABC):

    @abc.abstractmethod
    def annotate(self, data: List[gpd.GeoDataFrame], raster: np.array, **kwargs) -> Geometry:
        """
        Annotate data
        :param data: Input data to annotate
        :param raster: Input raster grid
        :return: Holoviews Geometry to overlay
        """
        pass
