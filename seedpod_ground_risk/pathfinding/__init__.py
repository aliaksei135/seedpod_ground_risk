import numpy as np
from skimage.draw import line

from seedpod_ground_risk.pathfinding.environment import Node, GridEnvironment


def _euc_dist(n1, n2):
    return ((n1.position[0] - n2.position[0]) ** 2 + (n1.position[1] - n2.position[1]) ** 2) ** 0.5


def get_path_costs(path, env):
    ys = []
    for idx in range(len(path[:-1])):
        if type(path[idx]) is Node:
            n0 = path[idx].position
            n1 = path[idx + 1].position
        else:
            n0 = path[idx]
            n1 = path[idx + 1]
        l = line(n0[0], n0[1], n1[0], n1[1])
        if type(env) is GridEnvironment:
            ys.append(env.grid[l[0], l[1]])
        else:
            ys.append(env[l[0], l[1]])
    return np.hstack(ys)


def get_path_risk_sum(path, env: GridEnvironment):
    return np.sum(get_path_costs(path, env))


def get_path_risk_mean(path, env: GridEnvironment):
    return np.mean(get_path_costs(path, env))


def get_path_distance(path):
    dist = 0
    for prev, curr in zip(path, path[1:]):
        if type(prev) is Node:
            dist += _euc_dist(prev, curr)
        else:
            dist += ((prev[0] - curr[0]) ** 2 + (prev[1] - curr[1]) ** 2) ** 0.5
    return dist
