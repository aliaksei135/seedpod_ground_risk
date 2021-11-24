from heapq import heappop, heappush

cimport

cython
cimport

numpy as np

np.import_array()
# import numpy as np
from skimage.draw import line

from environment cimport Node, GridEnvironment

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.binding(False)
cdef float euc_dist(Node n1, Node n2):
    return ((n1.position[0] - n2.position[0]) ** 2 + (n1.position[1] - n2.position[1]) ** 2) ** 0.5

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.binding(False)
cdef list reconstruct_path(Node end, np.ndarray grid):
    cdef list reverse_path = []
    reverse_path_append = reverse_path.append
    cdef Node node = end
    while node is not None:
        reverse_path_append(node)
        if node.parent is None:
            break
        if node == node.parent:
            break
        node = node.parent
    path = list(reversed(reverse_path))
    return path

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.binding(False)
cdef float edge_cost(Node best, Node child, np.ndarray grid, float target_rpd):
    cdef float dist = euc_dist(best, child)
    cdef np.ndarray node_costs;
    if dist < 1.5:  # if adjacent don't use bresenham
        node_costs = grid[(best.position[0], child.position[0]), (best.position[1], child.position[1])]
    else:
        l = line(best.position[0], best.position[1], child.position[0], child.position[1])
        node_costs = grid[l[0], l[1]]

    # l = wu.draw_line(*child.position, *best.position)
    # l = np.delete(l, np.nonzero((l[:, 0] >= grid.shape[0]) | (l[:, 1] >= grid.shape[1])), axis=0)
    # node_costs = grid[l[:, 0].astype(int), l[:, 1].astype(int)] * l[:, 2]
    cdef float cost_mean = node_costs.mean()

    # rpd = (cost*self.gm)/dist
    cdef float k = cost_mean / target_rpd
    cdef float cost = cost_mean * dist

    return dist + (k * cost)

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
@cython.binding(False)
cdef (float, bint) calc_cost(Node child, Node best, np.ndarray grid, float target_rpd):
    cdef float g1 = best.g + edge_cost(best, child, grid, target_rpd)
    cdef float g2 = best.parent.g + edge_cost(best.parent, child, grid, target_rpd)
    if g2 <= g1:
        return g2, True
    else:
        return g1, False

cdef class RiskThetaStar:
    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.nonecheck(False)
    @staticmethod
    def find_path(GridEnvironment environment, Node start, Node end, float thres=3e-8):
        cdef np.ndarray grid = environment.grid.copy()
        # if thres <= grid.min():
        #     thres = grid.min()
        gm = grid.max()
        if gm != 0:
            grid = grid / gm
        target_rpd = thres / gm

        # Use heapq;the thread safety provided by PriorityQueue is not needed, as we only exec on a single thread
        cdef list open = [start]
        start.f = start.g = start.h = 0
        start.parent = start
        cdef dict open_cost = {start: edge_cost(start, end, grid, target_rpd)}
        cdef set closed = set()
        cdef Node node;
        cdef float cost;
        cdef Node parent;
        cdef Node neighbour;
        cdef bint is_parent;

        while open:
            node = heappop(open)
            if node in open_cost:
                open_cost.pop(node)
            else:
                continue
            closed.add(node)
            if node == end:
                return reconstruct_path(node, grid)

            for neighbour in environment.get_neighbours(node):
                if neighbour in closed:
                    continue
                cost, is_parent = calc_cost(neighbour, node, grid, target_rpd)
                if neighbour in open_cost and cost < neighbour.g:
                    del open_cost[neighbour]
                neighbour.g = cost

                if is_parent:
                    neighbour.parent = node.parent
                else:
                    neighbour.parent = node
                neighbour.f = cost + euc_dist(neighbour, end)
                heappush(open, neighbour)
                open_cost[neighbour] = neighbour.f

        return None
