import numpy as np


class Node:
    position: (int, int)
    parent: 'Node'
    f: float
    g: float
    h: float

    def __init__(self, position: (int, int), parent=None):
        self.position = position
        self.parent = parent

        self.f = 1e99
        self.g = 1e99
        self.h = 1e99

    def __eq__(self, other):
        return other.position == self.position

    def __lt__(self, other):
        return self.f < other.f

    def __hash__(self):
        return hash(self.position)


class GridEnvironment:
    grid: np.ndarray
    shape: (int, int)
    diagonals: bool
    graph: dict

    def __init__(self, grid, diagonals=False):
        self.grid = grid
        self.shape = grid.shape
        self.diagonals = diagonals
        self.graph = dict()

    def get_neighbours(self, node: Node):
        return self._find_neighbours(node.position)

    def _generate_graph(self):

        graph = {}

        for idx, orig_val in np.ndenumerate(self.grid):
            neighbours = self._find_neighbours(idx)
            graph[Node((idx[0], idx[1]))] = neighbours

        return graph

    def _find_neighbours(self, idx: (int, int)):
        has_top = has_bottom = has_left = has_right = False
        neighbours = set()
        max_y, max_x = self.shape

        # Offset into edge
        # max_y = max_y - 1
        # max_x = max_x - 1

        def eval_node(y, x):
            val = self.grid[y, x]
            nonlocal neighbours
            if val >= 0 and np.isfinite(val):
                neighbours.add(Node((y, x)))

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
