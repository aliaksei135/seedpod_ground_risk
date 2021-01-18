from queue import PriorityQueue
from typing import List, Dict, Union

import numpy as np

from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import Environment, Node
from seedpod_ground_risk.pathfinding.heuristic import Heuristic, EuclideanHeuristic


class AStar(Algorithm):
    def __init__(self, heuristic: Heuristic = EuclideanHeuristic()):
        self.heuristic = heuristic.h

    def find_path(self, environment: Environment, start: Node, end: Node) -> Union[List[Node], None]:
        open = PriorityQueue()
        open.put((0, start), False)
        closed = {start: None}
        costs = np.full(environment.grid.shape, np.inf)
        costs[start.y, start.x] = 0
        debug_heuristic_cost = np.full(environment.grid.shape, np.inf)

        while not open.empty():
            node = open.get()[1]
            if node == end:
                import matplotlib.pyplot as mpl
                mpl.matshow(costs)
                mpl.matshow(debug_heuristic_cost)
                mpl.show()
                return self._reconstruct_path(end, closed)

            current_cost = costs[node.y, node.x]
            for neighbour in environment.get_neighbours(node):
                x, y = neighbour.x, neighbour.y
                cost = current_cost + environment.f_cost(node, neighbour) + self.heuristic(start, neighbour)
                if costs[y, x] > cost:
                    costs[neighbour.y, neighbour.x] = cost
                    h = self.heuristic(neighbour, end)
                    open.put((cost + h, neighbour))
                    debug_heuristic_cost[y, x] = h
                    closed[neighbour] = node
        return None

    def _reconstruct_path(self, end: Node, closed_list: Dict[Node, Node]) -> List[Node]:
        reverse_path = []
        reverse_path_append = reverse_path.append
        reverse_path_append(end)
        node = closed_list[end]
        while node is not None:
            reverse_path_append(node)
            node = closed_list[node]
        return list(reversed(reverse_path))
