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
        if not environment.diagonals:
            raise ValueError('JPS relies on a grid environment with diagonals')

        self.environment = environment
        self._max_y, self._max_x = self.environment.grid.shape[0] - 1, self.environment.grid.shape[1] - 1
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

        if not self._is_passable(ny, nx):
            return None

        if nx == self.goal.x and ny == self.goal.y:
            return Node(nx, ny, self.environment.grid[ny, nx])

        if dx and dy:
            # Diagonal case
            if (self._is_passable(nx - dx, ny + dy) and not self._is_passable(nx - dx, ny)) or \
                    (self._is_passable(nx + dx, ny - dy) and not self._is_passable(nx, ny - dy)):
                return Node(nx, ny, self.environment.grid[ny, nx])

            # Orthogonal searches
            if self._jump(ny, nx, dy, 0) or self._jump(ny, nx, 0, dx):
                return Node(nx, ny, self.environment.grid[ny, nx])
        else:
            # Orthogonal case
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
        if y < 0 or y > self._max_y or x < 0 or x > self._max_x:
            return False

        return self.environment.grid[y, x] != -1


class RiskJumpPointSearchAStar(JumpPointSearchAStar):

    def __init__(self, heuristic: Heuristic = ManhattanHeuristic(), jump_gap=0):
        if not isinstance(heuristic, EuclideanRiskHeuristic):
            raise ValueError('Risk based A* can only use Risk based heuristics')
        if not heuristic.environment.diagonals:
            raise ValueError('JPS relies on a grid environment with diagonals')
        super().__init__(heuristic)
        self._jump_gap = jump_gap
        self.heuristic_env_hash = hash(heuristic.environment)

    def find_path(self, environment: GridEnvironment, start: Node, end: Node) -> Union[List[Node], None]:
        if not environment.diagonals:
            raise ValueError('JPS relies on a grid environment with diagonals')
        if self.heuristic_env_hash != hash(environment):
            raise ValueError("Risk based heuristic and algorithm should have the same environment")

        self.environment = environment
        self._max_y, self._max_x = self.environment.grid.shape[0] - 1, self.environment.grid.shape[1] - 1
        self.goal = end

        # Check if start and goal are the same
        if start == end:
            return [start]

        # Use heapq;the thread safety provided by ProrityQueue is not needed, as we only exec on a single thread
        open = []
        closed = {start: None}
        costs = np.full(environment.grid.shape, np.inf)
        costs[start.y, start.x] = 0
        if __debug__:
            debug_heuristic_cost = np.full(environment.grid.shape, np.inf)

        for neighbour in environment.get_neighbours(start):
            h = self.heuristic(neighbour, end)
            heappush(open, (h, neighbour))
            closed[neighbour] = start
            costs[neighbour.y, neighbour.x] = self.heuristic(start, neighbour)
            if __debug__:
                debug_heuristic_cost[neighbour.y, neighbour.x] = h

        while open:

            node = heappop(open)[1]
            if node == end:
                if __debug__:
                    import matplotlib.pyplot as mpl
                    mpl.matshow(np.flipud(costs))
                    mpl.colorbar()
                    mpl.matshow(np.flipud(debug_heuristic_cost))
                    mpl.colorbar()
                    mpl.show()
                return self._reconstruct_path(end, closed)

            parent = closed[node]
            py, px = parent.y, parent.x
            cy, cx = node.y, node.x
            current_cost = costs[cy, cx]
            dy, dx = np.clip(cy - py, -1, 1), np.clip(cx - px, -1, 1)
            ny, nx = cy + dy, cx + dx
            # If the next node is not passable, the current node will be a dead end
            if not self._is_passable(ny, nx):
                continue
            jumpPoints = self._jump(cy, cx, dy, dx, self.environment.grid[ny, nx])

            if jumpPoints:
                for successor in jumpPoints:
                    x, y = successor.x, successor.y
                    cost = current_cost + self.heuristic(node, successor)
                    if costs[y, x] > cost:
                        costs[y, x] = cost
                        h = self.heuristic(successor, end)
                        heappush(open, (cost + h, successor))
                        closed[successor] = node
                        if __debug__:
                            debug_heuristic_cost[y, x] = h

        if __debug__:
            import matplotlib.pyplot as mpl
            mpl.matshow(np.flipud(costs))
            mpl.colorbar()
            mpl.matshow(np.flipud(debug_heuristic_cost))
            mpl.colorbar()
            mpl.show()
        return None

    def _jump(self, cy: int, cx: int, dy: int, dx: int, start_cost: float) -> List[Node]:
        ny, nx = cy + dy, cx + dx

        if not self._is_passable(ny, nx):
            return None

        if nx == self.goal.x and ny == self.goal.y:
            return [Node(nx, ny, self.environment.grid[ny, nx])]

        # Return as jump point if cost changes between nodes
        if abs(self.environment.grid[ny, nx] - start_cost) > self._jump_gap:
            return [Node(cx, cy, self.environment.grid[cy, cx])]

        if dx and dy:
            # Diagonal case
            if (self._is_passable(nx - dx, ny + dy) and not self._is_passable(nx - dx, ny)) or \
                    (self._is_passable(nx + dx, ny - dy) and not self._is_passable(nx, ny - dy)):
                return [Node(nx, ny, self.environment.grid[ny, nx])]

            # Orthogonal searches
            y_orthogonal_jump = self._jump(ny, nx, dy, 0, start_cost)
            x_orthogonal_jump = self._jump(ny, nx, 0, dx, start_cost)
            if y_orthogonal_jump or x_orthogonal_jump:
                jumps = [Node(nx, ny, self.environment.grid[ny, nx])]
                if y_orthogonal_jump:
                    jumps += y_orthogonal_jump
                if x_orthogonal_jump:
                    jumps += x_orthogonal_jump
                return jumps
        else:
            # Orthogonal case
            if dx:
                if (self._is_passable(nx, ny + 1) and not self._is_passable(nx - dx, ny + 1)) or \
                        (self._is_passable(nx, ny - 1) and not self._is_passable(nx - dx, ny - 1)):
                    return [Node(nx, ny, self.environment.grid[ny, nx])]
            else:  # dy
                if (self._is_passable(nx + 1, ny) and not self._is_passable(nx + 1, ny - dy)) or \
                        (self._is_passable(nx - 1, ny) and not self._is_passable(nx - 1, ny - dy)):
                    return [Node(nx, ny, self.environment.grid[ny, nx])]

        return self._jump(ny, nx, dy, dx, start_cost)
