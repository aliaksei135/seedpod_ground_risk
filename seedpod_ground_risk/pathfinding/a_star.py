from heapq import *
from typing import List, Dict, Union

import numpy as np

from seedpod_ground_risk.pathfinding import bresenham
from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import Node, GridEnvironment
from seedpod_ground_risk.pathfinding.heuristic import Heuristic, ManhattanHeuristic, RiskHeuristic


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
                return self._reconstruct_path(end, closed, environment.grid)

            current_cost = costs[node.y, node.x]
            for neighbour in environment.get_neighbours(node):
                x, y = neighbour.x, neighbour.y
                cost = current_cost + environment.f_cost(node, neighbour)
                if costs[y, x] > cost:
                    costs[neighbour.y, neighbour.x] = cost
                    heappush(open, (cost + self.heuristic(neighbour, end), neighbour))
                    closed[neighbour] = node
        return None

    def _reconstruct_path(self, end: Node, closed_list: Dict[Node, Node], grid: np.ndarray) -> List[Node]:
        reverse_path = []
        reverse_path_append = reverse_path.append
        reverse_path_append(end)
        node = closed_list[end]
        while node is not None:
            reverse_path_append(node)
            node = closed_list[node]
        path = list(reversed(reverse_path))

        # import matplotlib.pyplot as mpl
        # mpl.matshow(grid, cmap='jet')
        # mpl.colorbar()
        # mpl.plot([n.x for n in path], [n.y for n in path], color='red')
        # mpl.title(f'Full Path, length={len(path)}')
        # mpl.show()

        # return path

        # @jit(nopython=True, nogil=True)
        def get_path_sum(nx, ny, tx, ty, grid):
            line = bresenham.make_line(nx, ny, tx, ty)
            line_points = grid[line[:, 0], line[:, 1]]
            # If the new line crosses any blocked areas the cost is inf
            if -1 in line_points:
                return np.inf
            else:
                return line_points.sum()
            # integral_val = 0
            # for y, x in line:
            #     integral_val += grid[y, x]
            # return integral_val

        # @jit(nopython=True)
        def jump_path(node: Node, path, grid, goal: Node):
            nx, ny = node.x, node.y
            gx, gy = goal.x, goal.y
            if get_path_sum(nx, ny, gx, gy, grid) == 0:
                return goal

            path_idx = path.index(node) + 1
            test_node = init_node = path[path_idx]
            running_path_sum = get_path_sum(nx, ny, test_node.x, test_node.y, grid)
            while test_node != goal:
                px, py = test_node.x, test_node.y
                test_node = path[path_idx + 1]
                tx, ty = test_node.x, test_node.y
                running_path_sum += get_path_sum(px, py, tx, ty, grid)

                path_sum = get_path_sum(nx, ny, tx, ty, grid)

                if path_sum < running_path_sum:
                    return test_node
                else:
                    path_idx = path_idx + 1
            return init_node

        simplfied_path = []
        next_node = path[0]
        simplfied_path.append(next_node)
        while next_node != end:
            jump_node = jump_path(next_node, path, grid, end)
            simplfied_path.append(jump_node)
            next_node = jump_node

        # mpl.matshow(grid, cmap='jet')
        # mpl.colorbar()
        # mpl.plot([n.x for n in simplfied_path], [n.y for n in simplfied_path], color='red')
        # mpl.title(f'Simplified Path, length={len(simplfied_path)}')
        # mpl.show()

        return simplfied_path


class RiskGridAStar(GridAStar):

    def __init__(self, heuristic: Heuristic = ManhattanHeuristic()):
        if not isinstance(heuristic, RiskHeuristic):
            raise TypeError('Risk based A* can only use Risk based heuristics')
        super().__init__(heuristic)

    def find_path(self, environment: GridEnvironment, start: Node, end: Node) -> Union[List[Node], None]:
        # Use heapq;the thread safety provided by ProrityQueue is not needed, as we only exec on a single thread
        open = [(0, start)]
        # heappush(open, (0, start))
        closed = {start: None}
        costs = np.full(environment.grid.shape, np.inf)
        costs[start.y, start.x] = 0
        # if __debug__:
        #     debug_heuristic_cost = np.full(environment.grid.shape, np.inf)

        while open:
            node = heappop(open)[1]
            if node == end:
                # if __debug__:
                #     import matplotlib.pyplot as mpl
                #     mpl.matshow(costs)
                #     mpl.title('R A* g cost (start to node)')
                #     mpl.colorbar()
                #     # mpl.matshow(debug_heuristic_cost)
                #     # mpl.title('R A* h cost (node to goal)')
                #     # mpl.colorbar()
                #     mpl.show()
                return self._reconstruct_path(end, closed, environment.grid)

            current_cost = costs[node.y, node.x]
            for neighbour in environment.get_neighbours(node):
                x, y = neighbour.x, neighbour.y
                cost = current_cost + self.heuristic(node, neighbour)
                if costs[y, x] > cost:
                    costs[neighbour.y, neighbour.x] = cost
                    h = self.heuristic(neighbour, end)
                    heappush(open, (cost + h, neighbour))
                    closed[neighbour] = node
                    # if __debug__:
                    #     debug_heuristic_cost[y, x] = h

        # import matplotlib.pyplot as mpl
        # mpl.matshow(costs)
        # mpl.title('R A* g cost (start to node)')
        # mpl.colorbar()
        # mpl.matshow(debug_heuristic_cost)
        # mpl.title('R A* h cost (node to goal)')
        # mpl.colorbar()
        # mpl.show()

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
        # if __debug__:
        #     debug_heuristic_cost = np.full(environment.grid.shape, np.inf)

        while open:
            node = heappop(open)[1]
            if node == end:
                # if __debug__:
                #     import matplotlib.pyplot as mpl
                #     mpl.matshow(costs)
                #     mpl.matshow(debug_heuristic_cost)
                #     mpl.show()
                return self._reconstruct_path(end, closed, environment.grid)

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
                    # if __debug__:
                    #     debug_heuristic_cost[y, x] = h
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

        return self.environment.grid[y, x] > -1
