from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node


class Algorithm:
    def __init__(self, **kwargs):
        super().__init__()

    def find_path(self, environment: GridEnvironment, start: Node, goal: Node, **kwargs):
        pass
