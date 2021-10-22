from anytree import PreOrderIter
from anytree.exporter import JsonExporter
import os
from utils.operators import Assignment, IfThenElse

class Individual:

    def __init__(self, root, variables, max_depth=3, max_width=10):
        self.id = None
        self.root = root
        self.variables = variables
        self.max_depth = max_depth
        self.max_width = max_width
        self.lang = "c++"
        self.fitness = 0

    def add_variable(self, variables=None):
        if variables:
            self.variables.add(variables)

    def update_variable_registry(self, generate_random_expression):
        updated = False
        vars = []
        already_declared = [] #self.variables.variables_name()
        print("[{}] checking for program issues".format(self.id))
        # finding undeclared variables
        for node in PreOrderIter(self.root):
            print("[{}] node => \n{} \nis ass: {}, ifThenElse: {}".format(self.id, node, isinstance(node, Assignment), isinstance(node, IfThenElse)))
            if isinstance(node, Assignment):
                if node.declare == False and node.var.name not in self.variables.variables_name():
                    self.variables.register(node.var)
                    updated = True
                    vars.append(node.var)
                    already_declared.append(node.var.name)
                # elif node.declare == True:
                #     tmp_parent = node.parent
                    
                #     if node.var.name in already_declared:
                #         node.parent.children = []
                #     else:
                #         already_declared.append(node.var.name)
                #         node.parent = self.root
                    
                #     for c in node.children:
                #         c.parent = tmp_parent
            elif isinstance(node, IfThenElse):
                print("[{}] lf.name => {} rg.name => {} exp_t => {} {} exp_f => {} {} | {}".format(
                    self.id, 
                    node.condition.lf.name,
                    node.condition.rg.name,
                    isinstance(node.exp_t, Assignment),
                    node.exp_t.var.name,
                    isinstance(node.exp_f, Assignment),
                    node.exp_f.var.name,
                    self.variables.variables_name()
                ))
                if node.condition.lf.name not in self.variables.variables_name():
                    self.variables.register(node.condition.lf.name)
                    updated = True
                    vars.append(node.condition.lf.name)
                if node.condition.rg.name not in self.variables.variables_name():
                    self.variables.register(node.condition.rg.name)
                    updated = True
                    vars.append(node.condition.rg.name)
                if isinstance(node.exp_t, Assignment):
                    if node.exp_t.declare == False and node.exp_t.var.name not in self.variables.variables_name():
                        self.variables.register(node.exp_t.var)
                        updated = True
                        vars.append(node.exp_t.var)
                if isinstance(node.exp_f, Assignment):
                    if node.exp_f.declare == False and node.exp_f.var.name not in self.variables.variables_name():
                        self.variables.register(node.exp_f.var)
                        updated = True
                        vars.append(node.exp_f.var)
        
        print("[{}] VARS NOT DECLARED {}".format(self.id, [v.name for v in vars]))
        # declaring variables
        for var in vars:
            exp = generate_random_expression(self.variables)
            var_node = Assignment(var, exp, parent=self.root)
            # self.root.children.insert(0, var_node)

        # self.root.children

        return updated

    
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

        
