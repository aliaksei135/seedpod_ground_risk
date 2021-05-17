import random

import numpy as np
from skimage.draw import line

from seedpod_ground_risk.pathfinding.algorithm import Algorithm
from seedpod_ground_risk.pathfinding.environment import GridEnvironment, Node


def fitness_min_euclidean_length(max_val, path):
    dist = 0
    for n0, n1 in zip(path.enc_path, path.enc_path[1:]):
        dist += ((n0[0] - n1[1]) ** 2 + (n0[1] - n1[1]) ** 2) ** 0.5
    return dist / max_val


def fitness_min_manhattan_length(max_val, path):
    dist = 0
    for n0, n1 in zip(path.enc_path, path.enc_path[1:]):
        dist += abs(n0[0] - n1[1]) + abs(n0[1] - n1[1])
    return dist / max_val


def fitness_min_nodes(path):
    return len(path.get_path())


def fitness_min_energy(path):
    return 0


def fitness_correct_endpoints(start, end, path):
    if (path.enc_path[0] == start).all() and (path.enc_path[-1] == end).all():
        return 0
    return np.inf


def fitness_min_risk(grid, grid_max, path):
    # This also handles obstacle collisions as they are encoded as np.inf in the grid,
    # therefore summing with them gives np.inf as well
    risk = 0
    enc = path.enc_path
    for idx, n0 in enumerate(enc[:-1]):
        n1 = enc[idx + 1]
        l = line(n0[0], n0[1], n1[0], n1[1])
        risk += grid[l[0], l[1]].sum()

    return risk / grid_max


class Path:
    """
    A representation of a path.

    The path is encoded as a list of 2-tuples encoding (x, y) coordinates of the path node
    """

    def __init__(self) -> None:
        super().__init__()
        self.path = []
        self.enc_path = None  # enc_path is always the most up to date version, path can be lagging
        self.f = np.inf

    def encode_path(self):
        path_len = len(self.path)
        enc_path = np.zeros((path_len, 2), dtype=int)
        for idx, coord in enumerate(self.path):
            enc_path[idx, :] = np.array(coord, dtype=int)
        self.enc_path = enc_path

    def decode_path(self):
        self.path = []
        for coord in self.enc_path:
            self.path.append((int(coord[0]), int(coord[1])))

    def get_path(self):
        self.decode_path()
        return self.path


class GeneticAlgorithm(Algorithm):

    def __init__(self, fitness_funcs, fitness_weights=None) -> None:
        super().__init__()

        self.population = []

        self.grid = None

        # lists of functions to call for fitness
        # all func should take a single Path arg
        # fitness func should return float of fitness value or 0 if constraints not met
        self.fitness = fitness_funcs
        if not fitness_weights:
            self.fitness_weights = np.ones(len(fitness_funcs))
        else:
            if len(fitness_weights) == len(fitness_funcs):
                self.fitness_weights = fitness_weights
            else:
                raise ValueError("The number of fitness weights must match the number of fitness funcs")

    def find_path(self, environment: GridEnvironment, start: Node, goal: Node, **kwargs):
        self.grid = environment.grid
        self.start = start.position
        self.end = goal.position

        path = self.run(**kwargs)

        return [Node(c) for c in path.enc_path]

    def initialise(self, population_size, path_length):

        ymax, xmax = self.grid.shape

        for _ in range(population_size):
            indiv = Path()
            indiv.path.append(self.start)
            for _ in range(path_length - 2):
                x = int(np.random.randint(0, xmax))
                y = int(np.random.randint(0, ymax))
                indiv.path.append((y, x))
            indiv.path.append(self.end)
            indiv.encode_path()
            self.population.append(indiv)

    def _eval_fitness(self, path):
        n_fitness = len(self.fitness)
        vfit = np.zeros(n_fitness)
        for i in range(n_fitness):
            vfit[i] = self.fitness[i](path)
        return (vfit * self.fitness_weights).sum()

    def select(self, selection_type='tournament'):
        selection = []
        selection_append = selection.append
        if selection_type == 'tournament':
            for _ in range(2 * len(self.population)):
                par1, par2 = random.sample(self.population, 2)
                sfit1 = self._eval_fitness(par1)
                sfit2 = self._eval_fitness(par2)
                if sfit1 > sfit2:
                    selection_append(par1)
                else:
                    selection_append(par2)
            return list(zip(selection[0::2], selection[1::2]))
        elif selection_type == 'roulette':
            pass
        else:  # elitist
            pass

    def crossover(self, candidates):
        """
        Single point crossover of parents
        :param candidates:
        :return:
        """
        xver = []
        for par1, par2 in candidates:
            n = min(par1.enc_path.shape[0], par2.enc_path.shape[0])
            x_point = np.random.randint(0, n - 1)
            child = Path()
            child.enc_path = np.vstack((par1.enc_path[0:x_point], par2.enc_path[x_point:]))
            xver.append(child)
        return xver

    def mutate(self, candidates, mutation_prob=0.2, mutation_type='cull'):
        """
        Mutate nodes in the path
        :param candidates:
        :param mutation_prob:
        :return:
        """
        mutants = []
        for cand in candidates:
            n = cand.enc_path.shape[0]
            mutant = Path()
            if mutation_type == 'cull':
                cull_mask = np.random.random(n) > mutation_prob
                cull_mask[0] = cull_mask[-1] = True  # do not cull start or end points
                mutant.enc_path = cand.enc_path[cull_mask]
                mutants.append(mutant)
            elif mutation_type == 'monotone':
                # if np.random.random() < mutation_prob or n < 4:
                ix1 = np.random.randint((n // 2) - 1) + 1
                ix2 = np.random.randint((n // 2) + 1, n - 2)
                x0, y0 = cand.enc_path[ix1]
                x1, y1 = cand.enc_path[ix2]
                l = line(x0, y0, x1, y1)
                coords = np.vstack((l[0], l[1])).T.astype(int)
                coords_mask = np.random.random(coords.shape[0]) > mutation_prob
                coords = coords[coords_mask]
                mutant.enc_path = np.vstack((cand.enc_path[0:ix1], coords, cand.enc_path[ix2:]))
                mutants.append(mutant)
                # else:
                #     mutants.append(cand)
        return mutants

    def run(self, generations=500, population_size=400, stagnant_generations_end=40, init_path_length=200, ):
        self.initialise(population_size, init_path_length)
        best_fit_path = Path()
        stagnant_gens = 0

        for gen in range(generations):
            print('Run generation ', gen)
            selection = self.select()
            xver = self.crossover(selection)
            mut = self.mutate(xver, mutation_type='cull')

            gen_fitness = {self._eval_fitness(p): p for p in mut}
            gen_best_fit = min(gen_fitness.keys())
            if gen_best_fit < best_fit_path.f:
                print('New Best Fitness:', gen_best_fit, '| Fitness Improvement ', best_fit_path.f - gen_best_fit)
                best_fit_path = gen_fitness[gen_best_fit]
                best_fit_path.f = gen_best_fit
                stagnant_gens = 0

            else:
                stagnant_gens += 1
                if stagnant_gens > stagnant_generations_end:
                    return best_fit_path
            self.population = mut
        return best_fit_path
