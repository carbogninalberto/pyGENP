import numpy as np
from anytree import PreOrderIter, RenderTree
from anytree.exporter import JsonExporter
import os
import copy
from core.registers import Variable
from core.types import Types
from utils.operators import Assignment, Div, IfThenElse, Termination

class Individual:

    def __init__(self, root, variables, max_depth=3, max_width=10):
        self.id = None
        self.root = root
        self.variables = variables
        self.max_depth = max_depth
        self.max_width = max_width
        self.lang = "c++"
        self.fitness = 0
        self.is_elite = False

    def add_variable(self, variables=None):
        if variables:
            self.variables.add(variables)

    def update_variable_registry(self, generate_random_expression):
        updated = False
        vars = []
        already_declared = [] #self.variables.variables_name()
        # print("\033[92m[{}] checking for program issues".format(self.id))
        # finding undeclared variables        
        for node in PreOrderIter(self.root):
            # print(node.children)
            if isinstance(node, Assignment):
                # vars.append(node.var)
                # to_move_up = []

                # print("\033[92m\t {}".format(node.var.name))
                # if node.declare == True:
                #     print("\033[92m\t\t >changing also parent")
                #     for c in node.children:
                #         if c != node:
                #             c.parent = node.parent
                #     node.parent = self.root
                    # to_move_up.append(node)
                    
                
                if node.declare == False and node.var.name not in self.variables.variables_name():
                    # print("\t\t {} not in {}".format(node.var.name, self.variables.variables_name()))
                    self.variables.register(node.var)
                    updated = True
                    vars.append(node.var)
                
                for n_exp in node.exp.nums:
                    if isinstance(n_exp, Termination):
                        # print("\t\t\t {} vars è {}".format(n_exp, self.variables.variables_name()))
                        if n_exp.value == node.var.name \
                            or n_exp.value not in self.variables.variables_name() \
                            or (node.declare == True and self.is_var(n_exp.value)):
                            n_exp.value = np.random.randint(-20, 20)
                            if n_exp.value == 0:
                                n_exp.value = 1
                        elif self.is_var(n_exp.value) and str(n_exp.value) not in self.variables.variables_name():
                            new_var = Variable(n_exp.value, n_exp.tp)
                            self.variables.register(new_var)
                            updated = True
                            vars.append(new_var)
                
                # for n in to_move_up:
                #     n.parent = self.root
                    # children = list(self.root.children)
                    # try:
                    #     children.remove(node)
                    # except Exception as e:
                    #     print("element not in children")
                    # children.insert(0, n)
                    # self.root.children = children
                    # children = n.children
                    # parent = n.parent
                    # root_children = self.root.children
                    # for r_c in self.root.children:
                    #     n

                    # for c in children:
                    #     c.parent = parent

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
                            # print("\t\t\t {} vars è {}".format(n_exp, self.variables.variables_name()))
                            if self.is_var(n_exp.value) and str(n_exp.value) not in self.variables.variables_name():
                                new_var = Variable(n_exp.value, n_exp.tp)
                                self.variables.register(new_var)
                                updated = True
                                vars.append(new_var)
                if isinstance(node.exp_f, Assignment):
                    if node.exp_f.declare == False and node.exp_f.var.name not in self.variables.variables_name():
                        # print("\t\t {} not in {}".format(node.exp_f.var.name, self.variables.variables_name()))
                        self.variables.register(node.exp_f.var)
                        updated = True
                        vars.append(node.exp_f.var)
                
                    for n_exp in node.exp_f.exp.nums:
                        if isinstance(n_exp, Termination):
                            # print("\t\t\t {} vars è {}".format(n_exp, self.variables.variables_name()))
                            if self.is_var(n_exp.value) and str(n_exp.value) not in self.variables.variables_name():
                                new_var = Variable(n_exp.value, n_exp.tp)
                                self.variables.register(new_var)
                                updated = True
                                vars.append(new_var)
        
        # print("[{}] VARS NOT DECLARED {}".format(self.id, [v.name for v in vars]))
        # declaring variables
        for var in vars:
            exp = Termination(np.random.randint(10, 2001)/100.0, Types.float) #generate_random_expression(self.variables)
            Assignment(var, exp, parent=self.root)
            # print(self.root.children)
            
            # children = list(self.root.children)
            # try:
            #     children.remove(var_node)
            # except Exception as e:
            #     print("element not in children")
            # children.insert(0, var_node)
            # self.root.children = children
            # self.root.children.insert(0, var_node)
        
        to_move_up = []
        
        for node in PreOrderIter(self.root):
            if isinstance(node, Assignment) and node.declare == True:
                # print("moving top {}".format(node.var.name))
                to_move_up.append(node)
 
        
        # update tree
        for node in to_move_up:
            for c in node.children:
                c.parent = node.parent
            node.parent = self.root

        # self.root.children
        # children_root = list(copy.deepcopy(self.root.children))[::-1]
        children_root = list(self.root.children)[::-1]
        for idx, c in enumerate(children_root):
            if idx > 0:
                c.parent = children_root[idx-1]
            else:
                c.parent = self.root

        # self.root.children = children_root

        for node in PreOrderIter(self.root):

            # fixing case more than one child
            if len(list(node.children)) > 1:
                children_root = list(node.children)[::-1]
                for idx, c in enumerate(children_root):
                    if idx > 0:
                        c.parent = children_root[idx-1]
                    else:
                        c.parent = node

        for node in PreOrderIter(self.root):

            # fixing case more than one child
            if len(list(node.children)) > 1:
                children_root = list(node.children)[::-1]
                for idx, c in enumerate(children_root):
                    if idx > 0:
                        c.parent = children_root[idx-1]
                    else:
                        c.parent = node
                    
        seen_declarations = ['tcb->m_segmentSize', 'tcb->m_cWnd', 'segmentsAcked']
        to_remove = []
        for node in PreOrderIter(self.root):
            if isinstance(node, Assignment):
                if node.declare == True and node.var.name not in seen_declarations:
                    seen_declarations.append(node.var.name)
                elif node.declare == False and node.var.name not in seen_declarations:
                    to_remove.append(node)
                elif node.declare == True and node.var.name in seen_declarations:
                    to_remove.append(node)
                # fixing not already declare vars
                for n_exp in node.exp.nums:
                    if isinstance(n_exp, Div):
                        for n_exp_div in n_exp.nums:
                            if isinstance(n_exp_div, Termination):
                                if (self.is_var(n_exp_div.value) and str(n_exp_div.value) not in seen_declarations) or node.declare == True:
                                    n_exp_div.value = np.random.randint(-20, 20)
                                    if n_exp_div.value == 0:
                                        n_exp_div.value = 1
                    if isinstance(n_exp, Termination):
                        if (self.is_var(n_exp.value) and str(n_exp.value) not in seen_declarations) or node.declare == True:
                            n_exp.value = np.random.randint(-20, 20)
                            if n_exp.value == 0:
                                n_exp.value = 1
            
            elif isinstance(node, IfThenElse):
                if node.condition.lf.name not in seen_declarations:
                    to_remove.append(node)
                if node.condition.rg.name not in seen_declarations:
                    to_remove.append(node)
                if isinstance(node.exp_t, Assignment):
                    if node.exp_t.var.name not in seen_declarations:
                        to_remove.append(node)
                    for n_exp in node.exp_t.exp.nums:
                        if isinstance(n_exp, Termination):
                            if self.is_var(n_exp.value) and str(n_exp.value) not in seen_declarations:
                                n_exp.value = np.random.randint(-20, 20)
                                if n_exp.value == 0:
                                    n_exp.value = 1
                    for n_to_check in PreOrderIter(node.exp_t):
                        if n_to_check.var.name not in seen_declarations:
                            to_remove.append(node)
                        for n_exp in n_to_check.exp.nums:
                            if isinstance(n_exp, Termination):
                                if self.is_var(n_exp.value) and str(n_exp.value) not in seen_declarations:
                                    n_exp.value = np.random.randint(-20, 20)
                                    if n_exp.value == 0:
                                        n_exp.value = 1

                if isinstance(node.exp_f, Assignment):
                    if node.exp_f.var.name not in seen_declarations:
                        to_remove.append(node)
                    for n_exp in node.exp_f.exp.nums:
                        if isinstance(n_exp, Termination):
                            if self.is_var(n_exp.value) and str(n_exp.value) not in seen_declarations:
                                n_exp.value = np.random.randint(-20, 20)
                                if n_exp.value == 0:
                                    n_exp.value = 1
                    for n_to_check in PreOrderIter(node.exp_f):
                        if n_to_check.var.name not in seen_declarations:
                            to_remove.append(node)
                        for n_exp in n_to_check.exp.nums:
                            if isinstance(n_exp, Termination):
                                if self.is_var(n_exp.value) and str(n_exp.value) not in seen_declarations:
                                    n_exp.value = np.random.randint(-20, 20)
                                    if n_exp.value == 0:
                                        n_exp.value = 1
        
        # remove items
        for node in to_remove:
            for c in node.children:
                c.parent = node.parent
            node.parent = None


        # to_move_up = []
        
        # for node in PreOrderIter(self.root):
        #     if isinstance(node, Assignment) and node.declare == True:
        #         print("moving top {}".format(node.var.name))
        #         to_move_up.append(node)
 
        
        # # update tree
        # for node in to_move_up:
        #     for c in node.children:
        #         c.parent = node.parent
        #     node.parent = self.root

        # children_root = list(self.root.children)[::-1]
        # for idx, c in enumerate(children_root):
        #     if idx > 0:
        #         c.parent = children_root[idx-1]
        #     else:
        #         c.parent = self.root



        # for node in PreOrderIter(self.root):

        #     # fixing case more than one child
        #     if len(list(node.children)) > 1:
        #         children_root = list(node.children)[::-1]
        #         for idx, c in enumerate(children_root):
        #             if idx > 0:
        #                 c.parent = children_root[idx-1]
        #             else:
        #                 c.parent = node


        # print("\n\n\n\033[94m{}\n\n\n".format(RenderTree(self.root)))
        # print("##############################################################")

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


        
