cimport numpy as np

np.import_array()

cdef np.ndarray _make_line_low(int x0, int y0, int x1, int y1);
cdef np.ndarray _make_line_high(int x0, int y0, int x1, int y1);
cdef np.ndarray make_line(int x0, int y0, int  x1, int y1);
