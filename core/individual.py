from anytree import PreOrderIter
from anytree.exporter import JsonExporter
import os
from utils.operators import Assignment

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
                # if isinstance(node, Assignment) and node.var.recall == 0 and node.declare == False:
                #     print('this node {} has recall 0'.format(str(node)))
                if isinstance(node, Assignment):# and node.var.recall > 0: # and node.declare == False:
                    lines.append(str(node))
                elif not isinstance(node, Assignment):
                    lines.append(str(node))
            else:
                exclude = False
        return lines

    def max_fitness(self, idx, fitness_function):
        self.fitness = fitness_function(idx, lines=self.render_code())
        return self.fitness

    def save_to_file(self, folder="snapshot", file="file.cc"):
        #exporter = JsonExporter(indent=2, sort_keys=True)
        #print(exporter.export(root))
        path = os.path.join(folder, file)
        lines = self.render_code()
        with open(path, 'w') as f:
            f.writelines(lines)
        f.close()

        
