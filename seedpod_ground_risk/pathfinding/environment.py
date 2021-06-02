import numpy as np


class Node:

    def __init__(self, position, parent=None):
        self.position = position
        self.parent = parent

        self.f = np.inf
        self.g = np.inf
        self.h = np.inf

    def __eq__(self, other):
        return other.position == self.position

    def __lt__(self, other):
        return self.f < other.f

    def __hash__(self):
        return hash(self.position)


class GridEnvironment:

    def __init__(self, grid: np.array, diagonals=False):
        self.grid = grid
        self.shape = np.array(grid.shape)
        self.diagonals = diagonals
        self.graph = None

    @staticmethod
    def f_cost(node, goal):
        # Simple Euclidean distance as movement cost
        return ((node[0] - goal[0]) ** 2 + (node[1] - goal[1]) ** 2) ** 0.5

    def get_neighbours(self, node):
        # if not self.graph:
        #     self.graph = self._generate_graph()
        # return self.graph[node]
        return self._find_neighbours(node.position)

    def _generate_graph(self):

        graph = {}

        for idx, orig_val in np.ndenumerate(self.grid):
            neighbours = self._find_neighbours(idx)
            graph[Node((idx[0], idx[1]))] = neighbours

        return graph

    def _find_neighbours(self, idx):
        has_top = has_bottom = has_left = has_right = False
        neighbours = set()
        max_y, max_x = self.shape
        # Offset into edge
        max_y = max_y - 1
        max_x = max_x - 1

        def eval_node(y, x):
            val = self.grid[y, x]
            nonlocal neighbours
            if val >= 0:
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
