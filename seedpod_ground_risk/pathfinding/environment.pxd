cimport numpy as np

cdef class Node:
    cdef public (int, int) position;
    cdef public Node parent;
    cdef public float f
    cdef public float g
    cdef public float h

cdef class GridEnvironment:
    cdef public np.ndarray grid
    cdef readonly (int, int) shape
    cdef readonly bint diagonals
    cdef readonly dict graph

    cpdef set get_neighbours(self, Node node);
    cpdef dict _generate_graph(self);
    cdef set _find_neighbours(self, (int, int) idx);
