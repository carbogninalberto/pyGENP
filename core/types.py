from utils.operators import Assignment, WildcardCode, Equality, \
    IfThenElse, Termination, Mul, Sum, Sub, Div


class DefaultConfig:
    TP_CPP = {
        "integer": "int",
        "float": "float",
        "boolean": "bool"
    }

    OPERATORS = {
        "assignment": Assignment,
        "ifthenelse": IfThenElse,
    }

    MATH_OPERATORS = {
        "mul": Mul,
        "sum": Sum,
        "sub": Sub,
        "div": Div
    }


class Types:
    integer = "int"
    float = "float"
    boolean = "bool"
    # self.expression = "expression"
    compatibility = {
        integer: [integer, float],
        boolean: [boolean],
        float: [float, integer]
    }

    @staticmethod
    def is_compatible(a, b):
        return True if a in Types.compatibility[b] else False

    @staticmethod
    def get_all():
        return [
            Types.integer,
            Types.float
        ]