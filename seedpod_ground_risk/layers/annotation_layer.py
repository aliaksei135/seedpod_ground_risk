import abc
from typing import List

import geopandas as gpd
from holoviews.element.geom import Geometry

from seedpod_ground_risk.layers.layer import Layer


class AnnotationLayer(Layer, abc.ABC):

    @abc.abstractmethod
    def annotate(self, data: List[gpd.GeoDataFrame], **kwargs) -> Geometry:
        """
        Annotate data
        :param data: Input data to annotate
        :return: Holoviews Geometry to overlay
        """
        pass
