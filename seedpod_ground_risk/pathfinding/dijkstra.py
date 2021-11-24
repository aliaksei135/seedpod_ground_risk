from heapq import *

import matplotlib.pyplot as mpl
import numpy as np

from seedpod_ground_risk.pathfinding import _euc_dist
from seedpod_ground_risk.pathfinding.a_star import _reconstruct_path
from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node


class Dijkstra(Algorithm):
    def find_path(self, environment: GridEnvironment, start: Node, goal: Node, **kwargs):
        grid = environment.grid
        max_dist = np.sqrt((grid.shape[0] ** 2) + (grid.shape[1] ** 2))
        grid = ((grid / grid.max()) * max_dist) + 1
        env_shape = environment.grid.shape
        costs = np.full(env_shape, np.inf)
        open = []
        closed = set()
        heappush(open, (0, start))
        start.parent = None
        costs[start.position] = 0

        for y in range(env_shape[0]):
            for x in range(env_shape[1]):
                pos = (y, x)
                if pos != start.position:
                    heappush(open, (np.inf, Node(pos)))

        while open:
            cost, node = heappop(open)
            if node in closed:
                continue
            closed.add(node)
            # if node == goal:
            #     return _reconstruct_path(goal, grid, smooth=False)
            for neighbour in environment.get_neighbours(node):
                if neighbour in closed:
                    continue
                curr_cost = cost + grid[node.position] + _euc_dist(node, neighbour) + _euc_dist(neighbour,
                                                                                                goal)
                prev_cost = costs[neighbour.position]
                if curr_cost < prev_cost:
                    costs[neighbour.position] = curr_cost
                    heappush(open, (curr_cost, neighbour))
                    if neighbour == goal:
                        goal.parent = node
                    else:
                        neighbour.parent = node

        fig = mpl.figure()
        ax = fig.add_subplot(111)
        g = ax.matshow(costs)
        fig.colorbar(g, ax=ax)
        fig.show()

        return _reconstruct_path(goal, environment.grid, smooth=False)
