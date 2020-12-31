from typing import List

from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import Environment, Node
from seedpod_ground_risk.pathfinding.heuristic import Heuristic, EuclideanHeuristic


class AStar(Algorithm):
    def __init__(self, heuristic: Heuristic = EuclideanHeuristic):
        self.heuristic = heuristic

    def find_path(self, environment: Environment, start: Node, end: Node) -> List[Node]:
        pass
