

class VariableRegistry:

    def __init__(self, variables):        
        self.variables = variables if variables else []

    def add(self, var):
        if isinstance(var, list):
            for v in var:
                self.variables.append(v)
        else:
            self.variables.append(var)


class OperatorRegistry:

    def __init__(self, operators):
        self.oprators = operators if operators else []

    def add(self, op):
        if isinstance(op, list):
            for o in op:
                self.oprators.append(o)
        else:
            self.oprators.append(op)

