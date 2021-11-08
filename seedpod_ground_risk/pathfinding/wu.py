import numpy as np
from numba import jit


# Reference: https://en.wikipedia.org/wiki/Xiaolin_Wu%27s_line_algorithm#Algorithm


@jit(nopython=True, nogil=True, cache=True, fastmath=True)
def ipart(x):
    return np.floor(x)


@jit(nopython=True, nogil=True, cache=True, fastmath=True)
def fpart(x):
    return x - np.floor(x)


@jit(nopython=True, nogil=True, cache=True, fastmath=True)
def rfpart(x):
    return 1 - fpart(x)


@jit(nopython=True, nogil=True, cache=True, fastmath=True)
def draw_line(x0: int, y0: int, x1: int, y1: int) -> np.array:
    out = []

    steep = abs(y1 - y0) > abs(x1 - x0)

    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1
    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0

    dx = x1 - x0
    dy = y1 - y0

    if dx == 0:
        gradient = 1
    else:
        gradient = dy / dx

    xend = np.round(x0)
    yend = y0 + gradient * (xend - x0)
    xgap = rfpart(x0 + 0.5)
    xpx11 = xend
    ypx11 = ipart(yend)

    if steep:
        out.append((ypx11, xpx11, rfpart(yend) * xgap))
        out.append((ypx11 + 1, xpx11, fpart(yend) * xgap))
    else:
        out.append((xpx11, ypx11, rfpart(yend) * xgap))
        out.append((xpx11, ypx11 + 1, fpart(yend) * xgap))

    intery = yend + gradient

    xend = np.round(x1)
    yend = y1 + gradient * (xend - x1)
    xgap = fpart(x1 + 0.5)
    xpx12 = xend
    ypx12 = ipart(yend)

    if steep:
        out.append((ypx12, xpx12, rfpart(yend) * xgap))
        out.append((ypx12 + 1, xpx12, fpart(yend) * xgap))
    else:
        out.append((xpx12, ypx12, rfpart(yend) * xgap))
        out.append((xpx12, ypx12 + 1, fpart(yend) * xgap))

    if steep:
        for x in range(xpx11 + 1, xpx12):
            out.append((ipart(intery), x, rfpart(intery)))
            out.append((ipart(intery) + 1, x, fpart(intery)))
            intery += gradient
    else:
        for x in range(xpx11 + 1, xpx12):
            out.append((x, ipart(intery), rfpart(intery)))
            out.append((x, ipart(intery) + 1, fpart(intery)))
            intery += gradient

    return np.array(out)
