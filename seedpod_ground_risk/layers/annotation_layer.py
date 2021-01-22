import abc
from typing import List, Dict, Tuple

import geopandas as gpd
import numpy as np
from holoviews.element.geom import Geometry

from seedpod_ground_risk.layers.layer import Layer


class AnnotationLayer(Layer, abc.ABC):

    @abc.abstractmethod
    def annotate(self, data: List[gpd.GeoDataFrame], raster_data: Tuple[Dict[str, np.array], np.array],
                 **kwargs) -> Geometry:
        """
        Annotate data
        :param data: Input data to annotate
        :param raster_data: Input raster data
        :return: Holoviews Geometry to overlay
        """
        pass
