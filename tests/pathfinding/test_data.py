import numpy as np

from seedpod_ground_risk.pathfinding.environment import Node

# 5x5
SMALL_TEST_GRID = np.array([
    [0, 1, 1, 3, 6],
    [2, 5, 12, 56, 56],
    [12, 34, 45, 45, 12],
    [10, 24, 30, 30, 10],
    [25, 12, 10, 2, 0]
])
SMALL_TEST_GRAPH_NO_DIAGONAL = {
    Node(0, 0, 0): {
        Node(1, 0, 1),
        Node(0, 1, 2)
    },
    Node(1, 0, 1): {
        Node(0, 0, 0),
        Node(2, 0, 1),
        Node(1, 1, 5)
    },
    Node(2, 0, 1): {
        Node(1, 0, 1),
        Node(3, 0, 3),
        Node(2, 1, 12)
    },
    Node(3, 0, 3): {
        Node(2, 0, 1),
        Node(4, 0, 6),
        Node(3, 1, 56)
    },
    Node(4, 0, 6): {
        Node(3, 0, 3),
        Node(4, 1, 56)
    },
    Node(0, 1, 2): {
        Node(1, 1, 5),
        Node(0, 0, 0),
        Node(0, 2, 12)
    },
    Node(1, 1, 5): {
        Node(0, 1, 2),
        Node(2, 1, 12),
        Node(1, 0, 1),
        Node(1, 2, 34)
    },
    Node(2, 1, 12): {
        Node(1, 1, 5),
        Node(3, 1, 56),
        Node(2, 0, 1),
        Node(2, 2, 45)
    },
    Node(3, 1, 56): {
        Node(2, 1, 12),
        Node(4, 1, 56),
        Node(3, 0, 3),
        Node(3, 2, 45)
    },
    Node(4, 1, 56): {
        Node(3, 1, 56),
        Node(4, 0, 6),
        Node(4, 2, 12)
    },
    Node(0, 2, 12): {
        Node(1, 2, 34),
        Node(0, 1, 2),
        Node(0, 3, 10)
    },
    Node(1, 2, 34): {
        Node(0, 2, 12),
        Node(2, 2, 45),
        Node(1, 1, 5),
        Node(1, 3, 24)
    },
    Node(2, 2, 45): {
        Node(1, 2, 34),
        Node(3, 2, 45),
        Node(2, 1, 12),
        Node(2, 3, 30)
    },
    Node(3, 2, 45): {
        Node(2, 2, 45),
        Node(4, 2, 12),
        Node(3, 1, 56),
        Node(3, 3, 30)
    },
    Node(4, 2, 12): {
        Node(3, 2, 45),
        Node(4, 1, 56),
        Node(4, 3, 10)
    },
    Node(0, 3, 10): {
        Node(1, 3, 24),
        Node(0, 2, 12),
        Node(0, 4, 25)
    },
    Node(1, 3, 24): {
        Node(0, 3, 10),
        Node(2, 3, 30),
        Node(1, 2, 34),
        Node(1, 4, 12)
    },
    Node(2, 3, 30): {
        Node(1, 3, 24),
        Node(3, 3, 30),
        Node(2, 2, 45),
        Node(2, 4, 10)
    },
    Node(3, 3, 30): {
        Node(2, 3, 30),
        Node(4, 3, 10),
        Node(3, 2, 45),
        Node(3, 4, 2)
    },
    Node(4, 3, 10): {
        Node(3, 3, 30),
        Node(4, 2, 12),
        Node(4, 4, 0)
    },
    Node(0, 4, 25): {
        Node(1, 4, 12),
        Node(0, 3, 10)
    },
    Node(1, 4, 12): {
        Node(0, 4, 25),
        Node(2, 4, 10),
        Node(1, 3, 24)
    },
    Node(2, 4, 10): {
        Node(1, 4, 12),
        Node(3, 4, 2),
        Node(2, 3, 30)
    },
    Node(3, 4, 2): {
        Node(2, 4, 10),
        Node(4, 4, 0),
        Node(3, 3, 30)
    },
    Node(4, 4, 0): {
        Node(3, 4, 2),
        Node(4, 3, 10)
    }
}

LARGE_TEST_GRID = np.genfromtxt('costmap.csv', delimiter=',')

# 5x5
SMALL_DEADEND_TEST_GRID = np.array([
    [0, 1, -1, 3, 6],
    [2, 5, -1, 56, 56],
    [-1, -1, -1, 45, 12],
    [10, 24, 30, 30, 10],
    [25, 12, 10, 2, 0]
])
