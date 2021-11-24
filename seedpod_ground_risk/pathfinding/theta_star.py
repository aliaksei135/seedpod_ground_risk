from heapq import heappop, heappush
from typing import Union, List

import numpy as np
from skimage.draw import line

from seedpod_ground_risk.pathfinding import _euc_dist
from seedpod_ground_risk.pathfinding.a_star import _reconstruct_path
from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import Node, GridEnvironment


class RiskThetaStar(Algorithm):

    def find_path(self, environment: GridEnvironment, start: Node, end: Node, thres: float = 3e-8, **kwargs) \
            -> Union[List[Node], None]:
        grid = np.copy(environment.grid)
        gm = grid.max()
        if gm != 0:
            grid = grid / gm
        self.target_rpd = thres / gm

        env_shape = environment.grid.shape
        costs = np.full(env_shape, np.inf)
        hs = np.full(env_shape, np.inf)
        fs = np.full(env_shape, np.inf)

        # Use heapq;the thread safety provided by PriorityQueue is not needed, as we only exec on a single thread
        open = [start]
        start.f = start.g = start.h = 0
        start.parent = start
        open_cost = {start: self._edge_cost(start, end, grid)}
        closed = set()

        while open:
            node = heappop(open)
            if node in open_cost:
                open_cost.pop(node)
            else:
                continue
            closed.add(node)
            if node == end:
                # driv = np.full(env_shape, -1)
                # driv[costs > hs] = 1
                #
                # gs = mpl.GridSpec(2, 2, hspace=0.6)
                # fig = mpl.figure()
                # ax = fig.add_subplot(gs[0, 0])
                # ax.set_title('g costs')
                # ax2 = fig.add_subplot(gs[0, 1])
                # ax2.set_title('h costs')
                # ax3 = fig.add_subplot(gs[1, 0])
                # ax3.set_title('f costs')
                # ax4 = fig.add_subplot(gs[1, 1])
                # ax4.set_title('driving cost\ng>h?1:-1')
                # g = ax.matshow(costs)
                # fig.colorbar(g, ax=ax)
                # h = ax2.matshow(hs)
                # fig.colorbar(h, ax=ax2)
                # f = ax3.matshow(fs)
                # fig.colorbar(f, ax=ax3)
                # d = ax4.matshow(driv)
                # fig.colorbar(d, ax=ax4)
                # # fig.show()
                # mpl.close(fig)

                return _reconstruct_path(node, grid, smooth=False)

            for neighbour in environment.get_neighbours(node):
                if neighbour in closed:
                    continue
                cost, parent = self._calc_cost(neighbour, node, grid)
                if neighbour in open_cost and cost < neighbour.g:
                    del open_cost[neighbour]
                neighbour.g = cost

                neighbour.parent = parent
                h = _euc_dist(neighbour, end)
                neighbour.f = cost + h
                costs[neighbour.position] = cost
                hs[neighbour.position] = h
                fs[neighbour.position] = neighbour.f
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
        dist = _euc_dist(best, child)
        if dist < 1.5:  # if adjacent don't use bresenham
            node_costs = grid[(best.position[0], child.position[0]), (best.position[1], child.position[1])]
        else:
            l = line(best.position[0], best.position[1], child.position[0], child.position[1])
            node_costs = grid[l[0], l[1]]

        cost_mean = np.mean(node_costs)

        k = cost_mean / self.target_rpd
        cost = cost_mean * dist

        return dist + (k * cost)
