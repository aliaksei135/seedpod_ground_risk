from heapq import *
from typing import List, Dict, Union

import numpy as np

from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import Environment, Node
from seedpod_ground_risk.pathfinding.heuristic import Heuristic, EuclideanRiskHeuristic, \
    ManhattanHeuristic


class GridAStar(Algorithm):
    def __init__(self, heuristic: Heuristic = ManhattanHeuristic()):
        self.heuristic = heuristic.h

    def find_path(self, environment: Environment, start: Node, end: Node) -> Union[List[Node], None]:
        # Use heapq;the thread safety provided by ProrityQueue is not needed, as we only exec on a single thread
        open = []
        heappush(open, (0, start))
        closed = {start: None}
        costs = np.full(environment.grid.shape, np.inf)
        costs[start.y, start.x] = 0

        while open:
            node = heappop(open)[1]
            if node == end:
                import matplotlib.pyplot as mpl
                mpl.matshow(costs)
                mpl.show()
                return self._reconstruct_path(end, closed)

            current_cost = costs[node.y, node.x]
            for neighbour in environment.get_neighbours(node):
                x, y = neighbour.x, neighbour.y
                cost = current_cost + environment.f_cost(node, neighbour)
                if costs[y, x] > cost:
                    costs[neighbour.y, neighbour.x] = cost
                    heappush(open, (cost + self.heuristic(neighbour, end), neighbour))
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


class RiskGridAStar(GridAStar):

    def __init__(self, heuristic: Heuristic = ManhattanHeuristic()):
        if not isinstance(heuristic, EuclideanRiskHeuristic):
            raise TypeError('Risk based A* can only use Risk based heuristics')
        super().__init__(heuristic)

    def find_path(self, environment: Environment, start: Node, end: Node) -> Union[List[Node], None]:
        # Use heapq;the thread safety provided by ProrityQueue is not needed, as we only exec on a single thread
        open = []
        heappush(open, (0, start))
        closed = {start: None}
        costs = np.full(environment.grid.shape, np.inf)
        costs[start.y, start.x] = 0
        debug_heuristic_cost = np.full(environment.grid.shape, np.inf)

        while open:
            node = heappop(open)[1]
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
                    heappush(open, (cost + h, neighbour))
                    debug_heuristic_cost[y, x] = h
                    closed[neighbour] = node
        return None
