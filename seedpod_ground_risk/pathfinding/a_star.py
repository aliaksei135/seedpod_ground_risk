from heapq import *
from typing import List, Union, Tuple

import numpy as np

from seedpod_ground_risk.pathfinding import bresenham
from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node
from seedpod_ground_risk.pathfinding.heuristic import Heuristic, ManhattanHeuristic


def _reconstruct_path(end: Node, grid: np.ndarray, smooth=True) -> List[Node]:
    reverse_path = []
    reverse_path_append = reverse_path.append
    reverse_path_append(end)
    node = end
    while node is not None:
        reverse_path_append(node)
        node = node.parent
    path = list(reversed(reverse_path))

    if not smooth:
        return path

    def get_path_sum(nx, ny, tx, ty, grid):
        line = bresenham.make_line(nx, ny, tx, ty)
        line_points = grid[line[:, 0], line[:, 1]]
        # If the new line crosses any blocked areas the cost is inf
        if -1 in line_points:
            return np.inf
        else:
            return line_points.sum()

    def jump_path(node: Node, path, grid, goal: Node):
        ny, nx = node.position
        gy, gx = goal.position
        if get_path_sum(nx, ny, gx, gy, grid) == 0:
            return goal
        start_node_index = path.index(node)
        next_node_index = start_node_index + 1

        for test_node_index in reversed(range(len(path))):
            # Ensure still looking forward from start node
            if test_node_index > next_node_index:
                ty, tx = path[test_node_index].position
                path_x = [p.position[1] for p in path[start_node_index:test_node_index]]
                path_y = [p.position[0] for p in path[start_node_index:test_node_index]]
                existing_path_sum = grid[path_y, path_x].sum()
                test_path_sum = get_path_sum(nx, ny, tx, ty, grid)
                if test_path_sum <= existing_path_sum:
                    return path[test_node_index]
        return path[next_node_index]

    simplfied_path = []
    next_node = path[0]
    simplfied_path.append(next_node)
    while next_node != end:
        jump_node = jump_path(next_node, path, grid, end)
        simplfied_path.append(jump_node)
        next_node = jump_node

    return simplfied_path


class GridAStar(Algorithm):
    def __init__(self, heuristic: Heuristic = ManhattanHeuristic()):
        self.heuristic = heuristic.h

    def find_path(self, environment: GridEnvironment, start: Node, end: Node) -> Union[
        List[Node], None]:
        pass


# Canonical algorithm from literature
class RiskAStar(Algorithm):

    def find_path(self, environment: GridEnvironment, start: Node, end: Node, k=0.9, smooth=True, **kwargs) -> Union[
        List[Node], None]:
        grid = environment.grid
        min_dist = 2 ** 0.5
        goal_val = grid[end.position]

        # Use heapq;the thread safety provided by PriorityQueue is not needed, as we only exec on a single thread
        open = [start]
        start.f = start.g = start.h = 0
        open_cost = {start: start.f}
        closed = set()

        while open:
            node = heappop(open)
            if node in open_cost:
                open_cost.pop(node)
            if node in closed:
                continue
            closed.add(node)
            if node == end:
                return _reconstruct_path(node, grid, smooth=smooth)

            current_cost = node.f
            node_val = grid[node.position]
            for neighbour in environment.get_neighbours(node):
                cost = current_cost \
                       + (((grid[neighbour.position] + node_val) / 2)
                          * (((node.position[1] - neighbour.position[1]) ** 2 + (
                                node.position[0] - neighbour.position[0]) ** 2) ** 0.5))
                if cost < neighbour.g:
                    neighbour.g = cost

                    dist = ((node.position[1] - end.position[1]) ** 2 + (
                            node.position[0] - end.position[0]) ** 2) ** 0.5
                    line = bresenham.make_line(node.position[1], node.position[0], end.position[1], end.position[0])
                    min_val = grid[line[:, 0], line[:, 1]].min()
                    node_val = grid[node.position]
                    h = k * ((((node_val + goal_val) / 2) * min_dist) + ((dist - min_dist) * min_val))

                    # h = self.heuristic(neighbour.position, end.position)
                    neighbour.h = h
                    neighbour.f = cost + h
                    neighbour.parent = node
                    if neighbour not in open_cost or neighbour.f < open_cost[neighbour]:
                        heappush(open, neighbour)
                        open_cost[neighbour] = neighbour.f

        return None


class RiskGridAStar(GridAStar):

    def find_path(self, environment: GridEnvironment, start: Node, end: Node, k=1, smooth=True, **kwargs) -> Union[
        List[Node], None]:
        grid = environment.grid

        # Use heapq;the thread safety provided by PriorityQueue is not needed, as we only exec on a single thread
        open = [start]
        start.f = start.g = start.h = 0
        open_cost = {start: start.f}
        closed = set()

        while open:
            node = heappop(open)
            if node in open_cost:
                open_cost.pop(node)
            if node in closed:
                continue
            closed.add(node)
            if node == end:
                return _reconstruct_path(node, grid, smooth=smooth)

            current_cost = node.f
            for neighbour in environment.get_neighbours(node):
                cost = current_cost + grid[neighbour.position]
                if cost < neighbour.g:
                    neighbour.g = cost
                    h = abs((node.position[0] - end.position[0])) + abs((node.position[1] - end.position[1]))
                    neighbour.h = h
                    neighbour.f = cost + (k * h)
                    neighbour.parent = node
                    if neighbour not in open_cost or neighbour.f < open_cost[neighbour]:
                        heappush(open, neighbour)
                        open_cost[neighbour] = neighbour.f

        return None


class JumpPointSearchAStar(GridAStar):

    def find_path(self, environment: GridEnvironment, start: Node, end: Node) -> Union[
        List[Node], None]:
        if not environment.diagonals:
            raise ValueError('JPS relies on a grid environment with diagonals')

        self.environment = environment
        grid = environment.grid
        self._max_y, self._max_x = self.environment.grid.shape[0] - 1, self.environment.grid.shape[1] - 1
        self.goal = end

        # Use heapq;the thread safety provided by ProrityQueue is not needed, as we only exec on a single thread
        open = [start]
        start.f = start.g = start.h = 0
        open_cost = {start: start.f}
        closed = set()

        while open:
            node = heappop(open)
            open_cost.pop(node)
            if node in closed:
                continue
            closed.add(node)
            if node == end:
                return _reconstruct_path(end, grid)

            current_cost = node.f
            cy, cx = node.position
            successors = []
            for neighbour in environment.get_neighbours(node):
                dx, dy = neighbour.position[1] - cx, neighbour.position[0] - cy
                jump_point = self._jump(cy, cx, dy, dx)
                if jump_point:
                    successors.append(Node(jump_point))

            for successor in successors:
                cost = current_cost + grid[successor.position]
                if cost < successor.g:
                    successor.g = cost
                    h = self.heuristic(successor.position, end.position)
                    successor.h = h
                    successor.f = h + cost
                    if successor not in open_cost or successor.f < open_cost[successor]:
                        heappush(open, successor)
                        open_cost[successor] = successor.f
        return None

    def _jump(self, cy: int, cx: int, dy: int, dx: int) -> Tuple[int, int]:
        ny, nx = cy + dy, cx + dx

        if not self._is_passable(ny, nx):
            return None

        if nx == self.goal[1] and ny == self.goal[0]:
            return ny, nx

        if dx and dy:
            # Diagonal case
            if (self._is_passable(nx - dx, ny + dy) and not self._is_passable(nx - dx, ny)) or \
                    (self._is_passable(nx + dx, ny - dy) and not self._is_passable(nx, ny - dy)):
                return ny, nx

            # Orthogonal searches
            if self._jump(ny, nx, dy, 0) or self._jump(ny, nx, 0, dx):
                return ny, nx
        else:
            # Orthogonal case
            if dx:
                if (self._is_passable(nx + dx, ny + 1) and not self._is_passable(nx, ny + 1)) or \
                        (self._is_passable(nx + dx, ny - 1) and not self._is_passable(nx, ny - 1)):
                    return ny, nx
            else:  # dy
                if (self._is_passable(nx + 1, ny + dy) and not self._is_passable(nx + 1, ny)) or \
                        (self._is_passable(nx - 1, ny + dy) and not self._is_passable(nx - 1, ny)):
                    return ny, nx

        return self._jump(ny, nx, dy, dx)

    def _is_passable(self, y, x):
        if y < 0 or y > self._max_y or x < 0 or x > self._max_x:
            return False

        return self.environment.grid[y, x] > -1
