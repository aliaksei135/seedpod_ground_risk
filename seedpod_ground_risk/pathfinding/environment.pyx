import numpy as np

cdef class Node:
    def __init__(self, (int, int) position, parent=None):
        self.position = position
        self.parent = parent

        self.f = 1e99
        self.g = 1e99
        self.h = 1e99

    def __eq__(self, Node other):
        return other.position == self.position

    def __lt__(self, Node other):
        return self.f < other.f

    def __hash__(self):
        return hash(self.position)

cdef class GridEnvironment:
    def __init__(self, grid, bint diagonals=False):
        self.grid = grid
        self.shape = grid.shape
        self.diagonals = diagonals
        # self.graph = dict()

    cpdef set get_neighbours(self, Node node):
        return self._find_neighbours(node.position)

    cpdef dict _generate_graph(self):

        cdef dict graph = {}
        cdef (int, int) idx;
        cdef float orig_val;

        for idx, orig_val in np.ndenumerate(self.grid):
            neighbours = self._find_neighbours(idx)
            graph[Node((idx[0], idx[1]))] = neighbours

        return graph

    cdef set _find_neighbours(self, (int, int) idx):
        cdef bint has_top, has_bottom, has_left, has_right;
        has_top = has_bottom = has_left = has_right = False
        cdef set neighbours = set()
        cdef int max_y, max_x;
        max_y, max_x = self.shape

        # Offset into edge
        # max_y = max_y - 1
        # max_x = max_x - 1

        def eval_node(int y, int x):
            val = self.grid[y, x]
            nonlocal neighbours
            if val >= 0 and np.isfinite(val):
                neighbours.add(Node((y, x)))

        cdef int y, x;
        if idx[1] - 1 > 0:
            has_left = True
            y, x = idx[0], idx[1] - 1
            eval_node(y, x)
        if idx[1] + 1 < max_x:
            has_right = True
            y, x = idx[0], idx[1] + 1
            eval_node(y, x)
        if idx[0] - 1 > 0:
            has_top = True
            y, x = idx[0] - 1, idx[1]
            eval_node(y, x)
        if idx[0] + 1 < max_y:
            has_bottom = True
            y, x = idx[0] + 1, idx[1]
            eval_node(y, x)

        if self.diagonals:
            if has_top:
                y = idx[0] - 1
                if has_left:
                    x = idx[1] - 1
                    eval_node(y, x)
                if has_right:
                    x = idx[1] + 1
                    eval_node(y, x)
            if has_bottom:
                y = idx[0] + 1
                if has_left:
                    x = idx[1] - 1
                    eval_node(y, x)
                if has_right:
                    x = idx[1] + 1
                    eval_node(y, x)
        return neighbours
