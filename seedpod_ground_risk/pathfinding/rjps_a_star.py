from heapq import *
from typing import List, Union

import numpy as np

from seedpod_ground_risk.pathfinding.a_star import JumpPointSearchAStar, _reconstruct_path
from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node
from seedpod_ground_risk.pathfinding.heuristic import Heuristic, RiskHeuristic

global max_y, max_x


## Implementation is broken ##

def is_passable(grid, y, x):
    if y > max_y or x > max_x or y < 0 or x < 0:
        return False

    return grid[y, x] != -1


def jump(grid: np.ndarray, cy: int, cx: int, dy: int, dx: int, gy: int, gx: int, start_cost: float, jump_gap: float,
         jump_limit: float, jump_count: int) -> np.array:
    ny, nx = cy + dy, cx + dx
    out = np.full((3, 3), -1)

    if not is_passable(grid, ny, nx):
        return out

    if nx == gx and ny == gy:
        out[0, :] = [nx, ny, grid[ny, nx]]
        return out

    # Return as jump point if cost changes between s
    if abs(grid[ny, nx] - start_cost) > jump_gap:
        out[0, :] = [cx, cy, grid[cy, cx]]
        return out

    if jump_count > jump_limit:
        out[0, :] = [cx, cy, grid[cy, cx]]
        return out

    if dx and dy:
        # Diagonal case
        if (is_passable(grid, nx - dx, ny + dy) and not is_passable(grid, nx - dx, ny)) or \
                (is_passable(grid, nx + dx, ny - dy) and not is_passable(grid, nx, ny - dy)):
            out[0, :] = [nx, ny, grid[ny, nx]]
            return out

        # Orthogonal searches
        y_orthogonal_jump = jump(grid, ny, nx, dy, 0, gy, gx, start_cost, jump_gap, jump_limit, jump_count + 1)
        x_orthogonal_jump = jump(grid, ny, nx, 0, dx, gy, gx, start_cost, jump_gap, jump_limit, jump_count + 1)
        if not (y_orthogonal_jump == -1).all() or not (x_orthogonal_jump == -1).all():
            out[0, :] = [cx, cy, grid[cy, cx]]
            out[1, :] = x_orthogonal_jump[0, :]
            out[2, :] = y_orthogonal_jump[0, :]
            return out

    else:
        # Orthogonal case
        if dx:
            if (is_passable(grid, nx, ny + 1) and not is_passable(grid, nx - dx, ny + 1)) or \
                    (is_passable(grid, nx, ny - 1) and not is_passable(grid, nx - dx, ny - 1)):
                out[0, :] = [nx, ny, grid[ny, nx]]
                return out
        else:  # dy
            if (is_passable(grid, nx + 1, ny) and not is_passable(grid, nx + 1, ny - dy)) or \
                    (is_passable(grid, nx - 1, ny) and not is_passable(grid, nx - 1, ny - dy)):
                out[0, :] = [nx, ny, grid[ny, nx]]
                return out

    return jump(grid, ny, nx, dy, dx, gy, gx, start_cost, jump_gap, jump_limit, jump_count + 1)


class RiskJumpPointSearchAStar(JumpPointSearchAStar):

    def __init__(self, heuristic: Heuristic, jump_gap=0, jump_limit=200):
        raise NotImplementedError("Risk JPS A* no longer works")
        if not isinstance(heuristic, RiskHeuristic):
            raise ValueError('Risk based A* can only use Risk based heuristics')
        if not heuristic.environment.diagonals:
            raise ValueError('JPS relies on a grid environment with diagonals')
        super().__init__(heuristic)
        self.jump_gap = jump_gap
        self.jump_limit = jump_limit
        self.heuristic_env_hash = hash(heuristic.environment)

    def find_path(self, environment: GridEnvironment, start: Node, end: Node) -> Union[
        List[Node], None]:
        if not environment.diagonals:
            raise ValueError('JPS relies on a grid environment with diagonals')
        if self.heuristic_env_hash != hash(environment):
            raise ValueError("Risk based heuristic and algorithm should have the same environment")

        global max_y, max_x

        grid = environment.grid
        max_y, max_x = grid.shape[0] - 1, grid.shape[1] - 1
        self.goal = end

        # Check if start and goal are the same
        if start == end:
            return [start]

        # Use heapq;the thread safety provided by ProrityQueue is not needed, as we only exec on a single thread
        open = [start]
        start.f = start.g = start.h = 0
        open_cost = {start: start.f}
        closed = set()

        for neighbour in environment.get_neighbours(start):
            heappush(open, neighbour)
            closed[neighbour] = start
            neighbour = self.heuristic(start, neighbour)

        while open:

            node = heappop(open)

            if node == end:
                return _reconstruct_path(end, grid)

            parent = closed[node]
            py, px = parent[0], parent[1]
            cy, cx = node[0], node[1]
            current_cost = costs[cy, cx]
            dy, dx = np.clip(cy - py, -1, 1), np.clip(cx - px, -1, 1)
            ny, nx = cy + dy, cx + dx
            # If the next node is not passable, the current node will be a dead end
            if not is_passable(grid, ny, nx):
                continue
            jump_points = jump(grid, cy, cx, dy, dx, self.goal[0], self.goal[1], grid[ny, nx], self.jump_gap,
                               self.jump_limit, 0)

            for node_vals in jump_points:
                if (node_vals == -1).all():
                    continue
                x, y = node_vals[0], node_vals[1]
                successor = (y, x)
                cost = current_cost + self.heuristic(node, successor)
                if costs[y, x] > cost:
                    costs[y, x] = cost
                    h = self.heuristic(successor.position, end.position)
                    heappush(open, (cost + h, successor))
                    closed[successor] = node

        return None
