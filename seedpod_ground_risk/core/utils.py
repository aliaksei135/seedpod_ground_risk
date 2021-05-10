from typing import Iterable, Any

import numpy as np
from numpy.lib.stride_tricks import as_strided
from shapely import geometry as sg


def make_bounds_polygon(*args: Iterable[float]) -> sg.Polygon:
    if len(args) == 2:
        return sg.box(args[1][0], args[0][0], args[1][1], args[0][1])
    elif len(args) == 4:
        return sg.box(*args)


def is_null(values: Any) -> bool:
    from numpy import isnan

    try:
        for value in values:
            if value is None or isnan(value):
                return True
    except TypeError:
        if values is None or isnan(values):
            return True
    return False


def remove_raster_nans(raster):
    nans = np.isnan(raster)
    raster[nans] = 0
    return raster


# https://github.com/ilastik/lazyflow/blob/master/lazyflow/utility/blockwise_view.py
def block_split(arr, blockshape):
    blockshape = tuple(blockshape)
    outershape = tuple(np.array(arr.shape) // blockshape)
    view_shape = outershape + blockshape

    intra_block_strides = arr.strides

    inter_block_strides = tuple(arr.strides * np.array(blockshape))

    return as_strided(arr, shape=view_shape, strides=(inter_block_strides + intra_block_strides))
