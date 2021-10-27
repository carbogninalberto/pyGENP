import numpy as np
from anytree import PreOrderIter
from anytree.exporter import JsonExporter
import os
from core.registers import Variable
from core.types import Types
from utils.operators import Assignment, IfThenElse, Termination

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
            # print(node.children)
            if isinstance(node, Assignment):
                print("\t {}".format(node.var.name))
                if node.declare == False and node.var.name not in self.variables.variables_name():
                    print("\t\t {} not in {}".format(node.var.name, self.variables.variables_name()))
                    self.variables.register(node.var)
                    updated = True
                    vars.append(node.var)
                
                for n_exp in node.exp.nums:
                    if isinstance(n_exp, Termination):
                        print("\t\t\t {} vars è {}".format(n_exp, self.variables.variables_name()))
                        if self.is_var(n_exp.value) and str(n_exp.value) not in self.variables.variables_name():
                            new_var = Variable(n_exp.value, n_exp.tp)
                            self.variables.register(new_var)
                            updated = True
                            vars.append(new_var)

            elif isinstance(node, IfThenElse):
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
                        
                    for n_exp in node.exp_t.exp.nums:
                        if isinstance(n_exp, Termination):
                            print("\t\t\t {} vars è {}".format(n_exp, self.variables.variables_name()))
                            if self.is_var(n_exp.value) and str(n_exp.value) not in self.variables.variables_name():
                                new_var = Variable(n_exp.value, n_exp.tp)
                                self.variables.register(new_var)
                                updated = True
                                vars.append(new_var)
                if isinstance(node.exp_f, Assignment):
                    if node.exp_f.declare == False and node.exp_f.var.name not in self.variables.variables_name():
                        print("\t\t {} not in {}".format(node.exp_f.var.name, self.variables.variables_name()))
                        self.variables.register(node.exp_f.var)
                        updated = True
                        vars.append(node.exp_f.var)
                
                    for n_exp in node.exp_f.exp.nums:
                        if isinstance(n_exp, Termination):
                            print("\t\t\t {} vars è {}".format(n_exp, self.variables.variables_name()))
                            if self.is_var(n_exp.value) and str(n_exp.value) not in self.variables.variables_name():
                                new_var = Variable(n_exp.value, n_exp.tp)
                                self.variables.register(new_var)
                                updated = True
                                vars.append(new_var)

            # for n in PreOrderIter(n_exp):
            #     print('\t {}'.format(n.children))
            #     if isinstance(n, Termination):
            #         print(node.value)
            #         if node.value not in self.variables.variables_name():
            #             new_var = Variable(node.value, node.tp)
            #             self.variables.register(new_var)
            #             updated = True
            #             vars.append(new_var)
            # print("[{}] node => \n{} \nis ass: {}, ifThenElse: {}".format(self.id, node, isinstance(node, Assignment), isinstance(node, IfThenElse)))
            # if isinstance(node, Assignment):
            #     if node.declare == False and node.var.name not in self.variables.variables_name():
            #         self.variables.register(node.var)
            #         updated = True
            #         vars.append(node.var)
            #         already_declared.append(node.var.name)
            #     else:
            #         if node.declare == True:
            #             for c in node.children:
            #                 c.parent = node.parent
                        
            #             if node.var.name in already_declared:
            #                 node.parent.children = []
            #             else:
            #                 already_declared.append(node.var.name)
            #                 node.parent = self.root
                        
            #             node.parent = None
                    

            # elif isinstance(node, IfThenElse):
            #     # print("[{}] lf.name => {} rg.name => {} exp_t => {} {} exp_f => {} {} | {}".format(
            #     #     self.id, 
            #     #     node.condition.lf.name,
            #     #     node.condition.rg.name,
            #     #     isinstance(node.exp_t, Assignment),
            #     #     node.exp_t.var.name,
            #     #     isinstance(node.exp_f, Assignment),
            #     #     node.exp_f.var.name,
            #     #     self.variables.variables_name()
            #     # ))
            #     if node.condition.lf.name not in self.variables.variables_name():
            #         self.variables.register(node.condition.lf.name)
            #         updated = True
            #         vars.append(node.condition.lf.name)
            #     if node.condition.rg.name not in self.variables.variables_name():
            #         self.variables.register(node.condition.rg.name)
            #         updated = True
            #         vars.append(node.condition.rg.name)
            #     if isinstance(node.exp_t, Assignment):
            #         if node.exp_t.declare == False and node.exp_t.var.name not in self.variables.variables_name():
            #             self.variables.register(node.exp_t.var)
            #             updated = True
            #             vars.append(node.exp_t.var)
            #     if isinstance(node.exp_f, Assignment):
            #         if node.exp_f.declare == False and node.exp_f.var.name not in self.variables.variables_name():
            #             self.variables.register(node.exp_f.var)
            #             updated = True
            #             vars.append(node.exp_f.var)

        
        print("[{}] VARS NOT DECLARED {}".format(self.id, [v.name for v in vars]))
        # declaring variables
        for var in vars:
            exp = Termination(np.random.randint(10, 2001)/100.0, Types.float) #generate_random_expression(self.variables)
            var_node = Assignment(var, exp, parent=self.root)
            print(self.root.children)
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

    def is_var(self, value):
        value = "{}".format(value)
        try:
            if not value.isdigit():
                float(value)
            return False
        except Exception as e:
            return True

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

        
