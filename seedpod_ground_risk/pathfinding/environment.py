import abc
from typing import Dict, Sequence


class Node:
    def __init__(self, x, y, n, lon=0, lat=0):
        self.x = x
        self.y = y
        self.n = n

        self.lon = lon
        self.lat = lat


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
        return self.graph[node]

    @abc.abstractmethod
    def _generate_graph(self) -> Dict[Node, Sequence[Node]]:
        pass
