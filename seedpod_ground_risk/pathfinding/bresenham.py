import numpy as np
from numba import jit


# Reference: https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm

@jit(nopython=True, nogil=True)
def _make_line_low(x0: int, y0: int, x1: int, y1: int):
    dx = x1 - x0
    dy = y1 - y0
    my = max(y0, y1)
    yi = 1
    if dy < 0:
        yi = -1
        dy = -dy
    D = 2 * dy - dx
    y = y0
    n = dx + 1
    line = np.zeros((n, 2), dtype=np.int32)
    for idx, x in enumerate(range(x0, x1)):
        line[idx] = [y, x]
        if D > 0:
            y += yi
            if y > my:
                y = my
            D += 2 * (dy - dx)
        else:
            D += 2 * dy
    line[-1] = [y1, x1]
    return line


@jit(nopython=True, nogil=True)
def _make_line_high(x0: int, y0: int, x1: int, y1: int):
    dx = x1 - x0
    dy = y1 - y0
    mx = max(x0, x1)
    xi = 1
    if dx < 0:
        xi = -1
        dx = -dx
    D = 2 * dx - dy
    x = x0
    n = dy + 1
    line = np.zeros((n, 2), dtype=np.int32)
    for idx, y in enumerate(range(y0, y1)):
        line[idx] = [y, x]
        if D > 0:
            x += xi
            if x > mx:
                x = mx
            D += 2 * (dx - dy)
        else:
            D += 2 * dx
    line[-1] = [y1, x1]
    return line


@jit(nopython=True, nogil=True)
def make_line(x0: int, y0: int, x1: int, y1: int) -> np.array:
    """
    Return a rasterised line between pairs of coordinates on a 2d integer grid according to the Bresenham algorithm.

    Includes both start and end coordinates. Guaranteed to stay within the bounds set by endpoints.

    Returns a numpy array of (y,x) line coordinates with shape (n, 2) where n is the number of points in the line.

    :param x0: start x coordinate
    :param y0: start y coordinate
    :param x1: end x coordinate
    :param y1: end y coordinate
    :return: numpy array of (y,x) line coordinates
    """
    if abs(y1 - y0) < abs(x1 - x0):
        if x0 > x1:
            return _make_line_low(x1, y1, x0, y0)
        else:
            return _make_line_low(x0, y0, x1, y1)
    else:
        if y0 > y1:
            return _make_line_high(x1, y1, x0, y0)
        else:
            return _make_line_high(x0, y0, x1, y1)
