from environment cimport GridEnvironment, Node

cdef class Algorithm:
    def __init__(self, **kwargs):
        super().__init__()

    def find_path(self, GridEnvironment environment, Node start, Node goal, **kwargs):
        pass
