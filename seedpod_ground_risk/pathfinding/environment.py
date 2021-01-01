import abc
from typing import Dict, Sequence


class Node:
    def __init__(self, x, y, n, lon=0, lat=0):
        self.x = x
        self.y = y
        self.n = n

        self.lon = lon
        self.lat = lat

    def __eq__(self, other):
        if self.x == other.x and self.y == other.y and self.n == other.n:
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

    def __init__(self, grid: np.array, *args, diagonals=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid = grid
        self.diagonals = diagonals

    def f_cost(self, node: Node, goal: Node) -> float:
        # Simple Euclidean distance as movement cost
        return ((node.x - goal.x) ** 2 + (node.y - goal.y) ** 2) ** 0.5

    def _generate_graph(self) -> Dict[Node, Sequence[Node]]:
        import numpy as np

        graph = {}
        shape = self.grid.shape
        for idx, val in np.ndenumerate(self.grid):
            neighbours = []

            has_top = has_bottom = has_left = has_right = False

            if idx[1] - 1 >= 0:
                has_left = True
                left = Node(idx[1] - 1, idx[0], self.grid[idx[0], idx[1] - 1])
                neighbours.append(left)
            if idx[1] + 1 < shape[1]:
                has_right = True
                right = Node(idx[1] + 1, idx[0], self.grid[idx[0], idx[1] + 1])
                neighbours.append(right)
            if idx[0] - 1 >= 0:
                has_top = True
                top = Node(idx[1], idx[0] - 1, self.grid[idx[0] - 1, idx[1]])
                neighbours.append(top)
            if idx[0] + 1 < shape[0]:
                has_bottom = True
                bottom = Node(idx[1], idx[0] + 1, self.grid[idx[0] + 1, idx[1]])
                neighbours.append(bottom)

            if self.diagonals:
                if has_top:
                    if has_left:
                        topleft = Node(idx[1] - 1, idx[0] - 1, self.grid[idx[0] - 1, idx[1] - 1])
                        neighbours.append(topleft)
                    if has_right:
                        topright = Node(idx[1] + 1, idx[0] - 1, self.grid[idx[0] - 1, idx[1] + 1])
                        neighbours.append(topright)
                if has_bottom:
                    if has_left:
                        bottomleft = Node(idx[1] - 1, idx[0] + 1, self.grid[idx[0] + 1, idx[1] - 1])
                        neighbours.append(bottomleft)
                    if has_right:
                        bottomright = Node(idx[1] + 1, idx[0] + 1, self.grid[idx[0] + 1, idx[1] + 1])
                        neighbours.append(bottomright)

            node = Node(idx[1], idx[0], self.grid[idx[0], idx[1]])
            graph[node] = neighbours

        return graph

    def _print_environment(self):
        pass
