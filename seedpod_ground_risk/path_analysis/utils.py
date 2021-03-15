from typing import Tuple

import numpy as np
from numba import njit
from numba.np.arraymath import cross2d


@njit(cache=True)
def rotate_2d(vec: np.array, theta: float):
    """
    Rotate a 2D vector anticlockwise by a given angle
    :param vec: vector to rotate
    :param theta: angle in radians to rotate anticlockwise
    :return: rotated vector with same shape
    """
    if theta < 0:
        theta = 2 * np.pi - theta
    c, s = np.cos(theta), np.sin(theta)
    R = np.array(((c, -s), (s, c)))
    return cross2d(R, vec)


def snap_coords_to_grid(grid, lon: float, lat: float) -> Tuple[int, int]:
    """
    Snap coordinates to grid indices
    :param grid: raster grid coordinates
    :param lon: longitude to snap
    :param lat: latitude to snap
    :return: (x, y) tuple of grid indices
    """
    lat_idx = int(np.argmin(np.abs(grid['Latitude'] - lat)))
    lon_idx = int(np.argmin(np.abs(grid['Longitude'] - lon)))

    return lon_idx, lat_idx
