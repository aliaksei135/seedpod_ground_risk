import abc
from typing import Dict, Sequence

import numpy as np


class Node:
    x: int
    y: int
    n: float

    def __init__(self, x, y, n=0):
        self.x = x
        self.y = y
        self.n = n

    def __eq__(self, other):
        if self.x == other.x and self.y == other.y:
            return True
        return False

    def __hash__(self):
        return hash((self.x, self.y, self.n))

    def __lt__(self, other):
        return self.n < other.n

    def __str__(self):
        return f'Node at x={self.x}, y={self.y} with n={self.n}'


class Environment(abc.ABC):
    graph: Dict[Node, Sequence[Node]]

    def __init__(self, *args, **kwargs):
        self.graph = None

    def get_as_graph(self):
        if self.graph:
            return self.graph
        else:
            self.graph = self._generate_graph()
            return self.graph

    def get_neighbours(self, node: Node) -> Sequence[Node]:
        if not self.graph:
            self.graph = self._generate_graph()
        return self.graph[node]

    @abc.abstractmethod
    def f_cost(self, node: Node, goal: Node) -> float:
        pass

    @abc.abstractmethod
    def _generate_graph(self) -> Dict[Node, Sequence[Node]]:
        pass

    @abc.abstractmethod
    def _print_environment(self):
        pass


class GridEnvironment(Environment):
    import numpy as np

    grid: np.array

    def __init__(self, grid: np.array, *args, diagonals=False, pruning=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid = grid
        self.shape = self.grid.shape
        self.diagonals = diagonals
        self.pruning = pruning
        self._empty_nodes = np.full(grid.shape, False)

    def f_cost(self, node: Node, goal: Node) -> float:
        # Simple Euclidean distance as movement cost
        return ((node.x - goal.x) ** 2 + (node.y - goal.y) ** 2) ** 0.5

    def _generate_graph(self) -> Dict[Node, Sequence[Node]]:

        graph = {}

        for idx, orig_val in np.ndenumerate(self.grid):
            if self.pruning and self._empty_nodes[idx]:
                continue
            # elif self.grid[idx] == 0 and graph:
            #     self._empty_nodes[idx] = True
            #     continue

            neighbours = self._find_neighbours(idx, set())
            node = Node(idx[1], idx[0], self.grid[idx[0], idx[1]])
            graph[node] = neighbours

        return graph

    def _find_neighbours(self, idx, existing_neighbours):
        has_top = has_bottom = has_left = has_right = False
        neighbours = set(existing_neighbours)

        def eval_node(y, x):
            val = self.grid[y, x]
            nonlocal neighbours
            if self.pruning and val == 0:
                self._empty_nodes[y, x] = True
                neighbours.update(self._find_neighbours((y, x), neighbours))
            elif val >= 0:
                neighbours.add(Node(x, y, val))

        if idx[1] - 1 >= 0:
            has_left = True
            y, x = idx[0], idx[1] - 1
            eval_node(y, x)

        if idx[1] + 1 < self.shape[1]:
            has_right = True
            y, x = idx[0], idx[1] + 1
            eval_node(y, x)
        if idx[0] - 1 >= 0:
            has_top = True
            y, x = idx[0] - 1, idx[1]
            eval_node(y, x)
        if idx[0] + 1 < self.shape[0]:
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

    def _print_environment(self):
        pass
