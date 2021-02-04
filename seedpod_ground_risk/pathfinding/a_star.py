from heapq import *
from typing import List, Dict, Union

import numpy as np

from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import Node, GridEnvironment
from seedpod_ground_risk.pathfinding.heuristic import Heuristic, EuclideanRiskHeuristic, \
    ManhattanHeuristic


class GridAStar(Algorithm):
    def __init__(self, heuristic: Heuristic = ManhattanHeuristic()):
        self.heuristic = heuristic.h

    def find_path(self, environment: GridEnvironment, start: Node, end: Node) -> Union[List[Node], None]:
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

    def find_path(self, environment: GridEnvironment, start: Node, end: Node) -> Union[List[Node], None]:
        # Use heapq;the thread safety provided by ProrityQueue is not needed, as we only exec on a single thread
        open = []
        heappush(open, (0, start))
        closed = {start: None}
        costs = np.full(environment.grid.shape, np.inf)
        costs[start.y, start.x] = 0
        if __debug__:
            debug_heuristic_cost = np.full(environment.grid.shape, np.inf)

        while open:
            node = heappop(open)[1]
            if node == end:
                if __debug__:
                    import matplotlib.pyplot as mpl
                    mpl.matshow(np.flipud(costs))
                    mpl.matshow(np.flipud(debug_heuristic_cost))
                    mpl.show()
                return self._reconstruct_path(end, closed)

            # current_cost = costs[node.y, node.x]
            for neighbour in environment.get_neighbours(node):
                x, y = neighbour.x, neighbour.y
                cost = self.heuristic(start, neighbour)
                if costs[y, x] > cost:
                    costs[neighbour.y, neighbour.x] = cost
                    h = self.heuristic(neighbour, end)
                    heappush(open, (cost + h, neighbour))
                    closed[neighbour] = node
                    if __debug__:
                        debug_heuristic_cost[y, x] = h
        return None


class JumpPointSearchAStar(GridAStar):

    def find_path(self, environment: GridEnvironment, start: Node, end: Node) -> Union[List[Node], None]:
        self.environment = environment
        self._max_y, self._max_x = self.environment.grid.shape
        self.goal = end

        # Use heapq;the thread safety provided by ProrityQueue is not needed, as we only exec on a single thread
        open = []
        heappush(open, (0, start))
        closed = {start: None}
        costs = np.full(environment.grid.shape, np.inf)
        costs[start.y, start.x] = 0
        if __debug__:
            debug_heuristic_cost = np.full(environment.grid.shape, np.inf)

        while open:
            node = heappop(open)[1]
            if node == end:
                if __debug__:
                    import matplotlib.pyplot as mpl
                    mpl.matshow(costs)
                    mpl.matshow(debug_heuristic_cost)
                    mpl.show()
                return self._reconstruct_path(end, closed)

            cy, cx = node.y, node.x
            current_cost = costs[cy, cx]
            successors = []
            for neighbour in environment.get_neighbours(node):
                dx, dy = neighbour.x - cx, neighbour.y - cy
                jumpPoint = self._jump(cy, cx, dy, dx)
                if jumpPoint:
                    successors.append(jumpPoint)

            for successor in successors:
                x, y = successor.x, successor.y
                cost = current_cost + environment.f_cost(node, successor)
                if costs[y, x] > cost:
                    costs[y, x] = cost
                    h = self.heuristic(successor, end)
                    heappush(open, (cost + h, successor))
                    closed[successor] = node
                    if __debug__:
                        debug_heuristic_cost[y, x] = h
        return None

    def _jump(self, cy: int, cx: int, dy: int, dx: int) -> Node:
        ny, nx = cy + dy, cx + dx

        if self._is_passable(ny, nx):
            return None

        if nx == self.goal.x and ny == self.goal.y:
            return Node(nx, ny, self.environment.grid[ny, nx])

        if dx and dy:
            if (self._is_passable(nx - dx, ny + dy) and not self._is_passable(nx - dx, ny)) or \
                    (self._is_passable(nx + dx, ny - dy) and not self._is_passable(nx, ny - dy)):
                return Node(nx, ny, self.environment.grid[ny, nx])

            if self._jump(ny, nx, dy, 0) or self._jump(ny, nx, 0, dx):
                return Node(nx, ny, self.environment.grid[ny, nx])
        else:
            if dx:
                if (self._is_passable(nx + dx, ny + 1) and not self._is_passable(nx, ny + 1)) or \
                        (self._is_passable(nx + dx, ny - 1) and not self._is_passable(nx, ny - 1)):
                    return Node(nx, ny, self.environment.grid[ny, nx])
            else:  # dy
                if (self._is_passable(nx + 1, ny + dy) and not self._is_passable(nx + 1, ny)) or \
                        (self._is_passable(nx - 1, ny + dy) and not self._is_passable(nx - 1, ny)):
                    return Node(nx, ny, self.environment.grid[ny, nx])

        return self._jump(ny, nx, dy, dx)

    def _is_passable(self, y, x):
        if 0 > y > self._max_y or 0 > x > self._max_x:
            return False

        return self.environment.grid[y, x] != -1
