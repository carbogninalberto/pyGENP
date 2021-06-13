from anytree import Node

from core.individual import Individual


def generate_individual_from_seed(seed, max_depth=3, max_length=10):
    individual = Individual(max_depth=max_depth, max_length=max_length)
