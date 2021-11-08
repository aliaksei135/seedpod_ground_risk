import numpy as np


def dist(p1, p2):
    return np.sqrt(np.power(abs(p1[0] - p2[0]), 2) + np.power(abs(p1[1] - p2[1]), 2))


# 5x5
SMALL_TEST_GRID = np.array([
    [0, 1, 1, 3, 6],
    [2, 5, 12, 56, 56],
    [12, 34, 45, 45, 12],
    [10, 24, 30, 30, 10],
    [25, 12, 10, 2, 0]
], dtype=float)
SMALL_TEST_GRAPH_NO_DIAGONAL = {
    (0, 0): {
        (1, 0),
        (0, 1)
    },
    (1, 0): {
        (0, 0),
        (2, 0),
        (1, 1)
    },
    (2, 0): {
        (1, 0),
        (3, 0),
        (2, 1)
    },
    (3, 0): {
        (2, 0),
        (4, 0),
        (3, 1)
    },
    (4, 0): {
        (3, 0),
        (4, 1)
    },
    (0, 1): {
        (1, 1),
        (0, 0),
        (0, 2)
    },
    (1, 1): {
        (0, 1),
        (2, 1),
        (1, 0),
        (1, 2)
    },
    (2, 1): {
        (1, 1),
        (3, 1),
        (2, 0),
        (2, 2)
    },
    (3, 1): {
        (2, 1),
        (4, 1),
        (3, 0),
        (3, 2)
    },
    (4, 1): {
        (3, 1),
        (4, 0),
        (4, 2)
    },
    (0, 2): {
        (1, 2),
        (0, 1),
        (0, 3)
    },
    (1, 2): {
        (0, 2),
        (2, 2),
        (1, 1),
        (1, 3)
    },
    (2, 2): {
        (1, 2),
        (3, 2),
        (2, 1),
        (2, 3)
    },
    (3, 2): {
        (2, 2),
        (4, 2),
        (3, 1),
        (3, 3)
    },
    (4, 2): {
        (3, 2),
        (4, 1),
        (4, 3)
    },
    (0, 3): {
        (1, 3),
        (0, 2),
        (0, 4)
    },
    (1, 3): {
        (0, 3),
        (2, 3),
        (1, 2),
        (1, 4)
    },
    (2, 3): {
        (1, 3),
        (3, 3),
        (2, 2),
        (2, 4)
    },
    (3, 3): {
        (2, 3),
        (4, 3),
        (3, 2),
        (3, 4)
    },
    (4, 3): {
        (3, 3),
        (4, 2),
        (4, 4)
    },
    (0, 4): {
        (1, 4),
        (0, 3)
    },
    (1, 4): {
        (0, 4),
        (2, 4),
        (1, 3)
    },
    (2, 4): {
        (1, 4),
        (3, 4),
        (2, 3)
    },
    (3, 4): {
        (2, 4),
        (4, 4),
        (3, 3)
    },
    (4, 4): {
        (3, 4),
        (4, 3)
    }
}

import os

LARGE_TEST_GRID = np.genfromtxt(os.sep.join((os.path.dirname(os.path.realpath(__file__)), 'costmap.csv')),
                                delimiter=',')

# 5x5
SMALL_DEADEND_TEST_GRID = np.array([
    [0, 1, -1, 3, 6],
    [2, 5, -1, 56, 56],
    [-1, -1, -1, 45, 12],
    [10, 24, 30, 30, 10],
    [25, 12, 10, 2, 0]
])


def test_risk_square_grid():
    low_val = 1e-9
    high_val = 1e-7
    shape = (100, 100)

    grid = np.full(shape, low_val)
    grid[int(shape[0] * 0.3):int(shape[0] * 0.7), int(shape[1] * 0.3):int(shape[1] * 0.7)] = high_val
    return grid


TEST_RISK_SQUARE_GRID = test_risk_square_grid()


def test_risk_circle_grid():
    low_val = 1e-9
    high_val = 1e-7
    shape = (100, 100)
    radius = 20

    centre = (shape[0] // 2, shape[1] // 2)
    grid = np.full(shape, low_val)
    for idx, _ in np.ndenumerate(grid):
        if dist(centre, idx) <= radius:
            grid[idx] = high_val

    return grid


TEST_RISK_CIRCLE_GRID = test_risk_circle_grid()


def test_risk_circle2_grid():
    low_val = 1e-9
    mid_val = 1e-8
    high_val = 1e-7
    shape = (100, 100)
    inner_radius = 10
    outer_radius = 20

    centre = (shape[0] // 2, shape[1] // 2)
    grid = np.full(shape, low_val)
    for idx, _ in np.ndenumerate(grid):
        if dist(centre, idx) <= inner_radius:
            grid[idx] = high_val
        elif dist(centre, idx) <= outer_radius:
            grid[idx] = mid_val
    return grid


TEST_RISK_CIRCLE2_GRID = test_risk_circle2_grid()
