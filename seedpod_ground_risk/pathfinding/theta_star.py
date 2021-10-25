from heapq import heappop, heappush
from typing import Union, List

import numpy as np
from skimage.draw import line

from seedpod_ground_risk.pathfinding.a_star import _reconstruct_path
from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import Node, GridEnvironment
from seedpod_ground_risk.pathfinding.heuristic import Heuristic, ManhattanHeuristic


class RiskThetaStar(Algorithm):

    def __init__(self, heuristic: Heuristic = ManhattanHeuristic()):
        self.heuristic = heuristic.h

    def find_path(self, environment: GridEnvironment, start: Node, end: Node, smooth=False, k=0.9, thres=3e-8,
                  method=np.sum, **kwargs) -> Union[List[Node], None]:
        grid = environment.grid
        self.risk_threshold = thres
        self.cost_method = method
        self.max_cost = grid.max()
        self.max_dist = np.sqrt((grid.shape[0] ** 2) + (grid.shape[1] ** 2))

        # Use heapq;the thread safety provided by PriorityQueue is not needed, as we only exec on a single thread
        open = [start]
        start.f = start.g = start.h = 0
        start.parent = start
        open_cost = {start: self._euc_dist(start, end)}
        closed = set()

        while open:
            node = heappop(open)
            if node in open_cost:
                open_cost.pop(node)
            else:
                continue
            closed.add(node)
            if node == end:
                return _reconstruct_path(node, grid, smooth=smooth)

            for neighbour in environment.get_neighbours(node):
                if neighbour in closed:
                    continue
                cost, parent = self._calc_cost(neighbour, node, grid)
                if neighbour in open_cost and cost < neighbour.g:
                    del open_cost[neighbour]
                neighbour.g = cost
                neighbour.parent = parent
                neighbour.f = cost + (k * self._euc_dist(neighbour, node))
                heappush(open, neighbour)
                open_cost[neighbour] = neighbour.f

        return None

    def _calc_cost(self, child: Node, best: Node, grid):
        g1 = best.g + self._edge_cost(best, child, grid)
        g2 = best.parent.g + self._edge_cost(best.parent, child, grid)
        if g2 <= g1:
            return g2, best.parent
        else:
            return g1, best

    def _edge_cost(self, best, child, grid):
        dist = self._euc_dist(best, child)
        if dist < 1.5:  # if adjacent don't use bresenham
            node_costs = grid[(best.position[0], child.position[0]), (best.position[1], child.position[1])]
        else:
            l = line(best.position[0], best.position[1], child.position[0], child.position[1])
            node_costs = grid[l[0], l[1]]
        cost = self.cost_method(node_costs)
        if cost < self.risk_threshold:
            return 0
        return dist * cost

    def _euc_dist(self, n1, n2):
        return ((n1.position[0] - n2.position[0]) ** 2 + (n1.position[1] - n2.position[1]) ** 2) ** 0.5
