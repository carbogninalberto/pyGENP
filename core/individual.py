from registers import VariableRegistry, OperatorRegistry


class Individual:

    def __init__(self, root, operators=OperatorRegistry(), variables=VariableRegistry(), max_depth=3, max_width=10):
        self.root = root
        self.operators = operators
        self.variables = variables
        self.max_depth = max_depth
        self.max_width = max_width
        self.lang = "c++"

    def add(self, operators=None, variables=None):
        if operators:
            self.operators.add(operators)
        if variables:
            self.variables.add(variables)
    
    def render_code(self):
        lines = []
        for node in PreOrderIter(self.root):
            lines.append(str(node))
        return lines
