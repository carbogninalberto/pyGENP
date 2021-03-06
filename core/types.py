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
        "wildcardCode": WildcardCode
    }

    WILD_CARD_CODE = [
        ""
    ]

    MATH_OPERATORS = {
        "mul": Mul,
        "sum": Sum,
        "sub": Sub,
        "div": Div
    }

    TOURNAMENT = {
        "k": 60,
        "s": 15
    }

    MUTATION = {
        "operator_flip": 60,
        "switch_branches": 30,
        "switch_exp": 70,
        "truncate_node": 25, 
    }

    EQUALITY = {
        "lt": "<",
        "lte": "<=",
        "gt": ">",
        "gte": ">=",
        "eq": "==",
        "neq": "!="
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
