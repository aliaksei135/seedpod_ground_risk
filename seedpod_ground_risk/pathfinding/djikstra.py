from heapq import *

import numpy as np

from seedpod_ground_risk.pathfinding.a_star import _reconstruct_path
from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node


# import matplotlib.pyplot as mpl


class Djikstra(Algorithm):
    def find_path(self, environment: GridEnvironment, start: Node, goal: Node, **kwargs):
        env_shape = environment.grid.shape
        costs = np.full(env_shape, np.inf)
        open = []
        heappush(open, (0, start))
        start.parent = None

        for y in range(env_shape[0]):
            for x in range(env_shape[1]):
                pos = (y, x)
                if pos != start.position:
                    heappush(open, (np.inf, Node(pos)))

        while open:
            cost, node = heappop(open)
            for neighbour in environment.get_neighbours(node):
                curr_cost = cost + environment.grid[node.position]
                prev_cost = costs[neighbour.position]
                if curr_cost < prev_cost:
                    costs[neighbour.position] = curr_cost
                    if np.isinf(prev_cost):
                        heappush(open, (curr_cost, neighbour))
                    if neighbour == goal:
                        goal.parent = node
                    else:
                        neighbour.parent = node

        # fig = mpl.figure()
        # ax = fig.add_subplot(111)
        # g = ax.matshow(np.flip(costs))
        # fig.colorbar(g, ax=ax)
        # fig.show()

        return _reconstruct_path(goal, environment.grid, smooth=False)
