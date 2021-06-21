from anytree import PreOrderIter


class Individual:

    def __init__(self, root, variables, max_depth=3, max_width=10):
        self.root = root
        self.variables = variables
        self.max_depth = max_depth
        self.max_width = max_width
        self.lang = "c++"
        self.fitness = 0

    def add_variable(self, variables=None):
        if variables:
            self.variables.add(variables)
    
    def render_code(self):
        lines = []
        exclude = True
        for node in PreOrderIter(self.root):
            if not exclude:
                lines.append(str(node))
            else:
                exclude = False
        return lines

    def max_fitness(self, fitness_function):
        self.fitness = fitness_function(lines=self.render_code())
        return self.fitness
