import numpy as np


class Variable:

    def __init__(self, name=None, tp=None, scope=0):
        self.name = name
        self.tp = tp
        self.scope = scope

    def __str__(self):
        return self.name


class VariableRegistry:

    def __init__(self, variables):        
        self.variables = variables if variables else []

    def register(self, var):
        if isinstance(var, list):
            for v in var:
                self.variables.append(v)
        else:
            self.variables.append(var)
    
    def variables_name(self):
        return [v.name for v in self.variables]

    def get_random_var(self):
        #print("vars", self.variables)
        if isinstance(self.variables, list):
            if len(self.variables) > 0:
                return self.variables[np.random.randint(0, len(self.variables))]
            else:
                return self.variables
        else:
            return self.variables
    
    def is_there_compatible(self, types):
        if isinstance(self.variables, list):
            for var in self.variables:
                if var.tp in types:
                    return True
        else:
            if self.variables.tp in types:
                return True
        return False


class OperatorRegistry:

    def __init__(self, operators):
        self.operators = operators if operators else []

    def add(self, op):
        if isinstance(op, list):
            for o in op:
                self.operators.append(o)
        else:
            self.operators.append(op)

