from anytree import NodeMixin
from core.registers import Variable

class BaseTermination:

    def __init__(self, value, tp):
        self.value = value
        self.tp = tp

    def render_cpp(self):
        return "{}".format(self.value)
    
    def __str__(self):
        return self.render_cpp()


class Termination(BaseTermination, NodeMixin):
    '''
    This operator is the base of an "expression"
    '''

    def __init__(self, value, tp, parent=None, children=None):
        super(Termination, self).__init__(value, tp)
        self.name = super(Termination, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children
    
    def __str__(self):
        return self.render_cpp()


class BaseExpression:

    def __init__(self, root_exp):
        self.root_exp = root_exp

    def render_cpp(self):
        return "{}".format(self.root_exp)
    
    def __str__(self):
        return self.render_cpp()
    

class Expression:

    def __init__(self, root_exp, parent=None, children=None):
        super(Equality, self).__init__(root_exp)
        self.name = super(Equality, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children
    
    def __str__(self):
        return self.render_cpp()


class BaseEquality:

    def __init__(self, lf, rg, tp):
        self.lf = lf
        self.rg = rg
        self.type = tp

    def render_cpp(self):
        if self.type == "bool":
            return "{}".format(self.lf) # TODO: edit this
        return "{} {} {}".format(self.lf, self.type, self.rg)
    
    def __str__(self):
        return self.render_cpp()


class Equality(BaseEquality, NodeMixin):

    def __init__(self, lf=False, rg=False, tp="bool", parent=None, children=None):
        super(Equality, self).__init__(lf, rg, tp)
        self.name = super(Equality, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children
    
    def __str__(self):
        return self.render_cpp()


class BaseAssignment:
    
    def __init__(self, var, exp, declare):
        self.var = var
        self.exp = exp
        self.declare = declare

    def render_cpp(self):
        #print("---------> BaseAssignment var {}, exp {}, declare {}".format(str(self.var), str(self.exp), self.declare))
        #print("\t\t\t\t\tTP", self.var.tp if self.var else "empty var")
        tp = self.var.tp if self.var else ""
        return "{}{} = ({}) {};\n".format(tp + " " if self.declare else "", str(self.var), tp, self.exp)

    def __str__(self):
        return self.render_cpp()


class Assignment(BaseAssignment, NodeMixin):

    def __init__(self, var=None, exp=None, declare=True, parent=None, children=None):
        super(Assignment, self).__init__(var, exp, declare)
        self.name = super(Assignment, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children
    
    def __str__(self):
        return self.render_cpp()


class BaseIfThenElse:

    def __init__(self, condition, exp_t, exp_f):
        self.condition = condition
        self.exp_t = exp_t
        self.exp_f = exp_f
    
    def render_cpp(self):
        return "if ({}) {{\n\t{}\n}} else {{\n\t{}\n}}\n".format(self.condition, self.exp_t, self.exp_f)

    def __str__(self):
        return self.render_cpp()


class IfThenElse(BaseIfThenElse, NodeMixin):

    def __init__(self, condition=None, exp_t=None, exp_f=None, parent=None, children=None):
        super(IfThenElse, self).__init__(condition, exp_t, exp_f)
        self.name = super(IfThenElse, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children # [self.exp_t, self.exp_f]
    
    def __str__(self):
        return self.render_cpp()


class BaseWildcardCode:

    def __init__(self, code):
        self.code = code
    
    def render_cpp(self):
        return "{}\n".format(self.code)
    
    def __str__(self):
        return self.render_cpp()


class WildcardCode(BaseWildcardCode, NodeMixin):

    def __init__(self, code=None, parent=None, children=None):
        super(WildcardCode, self).__init__(code)
        self.name = super(WildcardCode, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children
    
    def __str__(self):
        return self.render_cpp()


# Math Operators

class BaseMul:
    
    def __init__(self, nums):
        self.nums = nums
    
    def render_cpp(self):
        code = "("
        for i, n in enumerate(self.nums):
            if i > 0:
                code += "*(" + str(n) + ")"
            else:
                code += str(n)
        code += ")"
        return code


class Mul(BaseMul, NodeMixin):
    def __init__(self, nums, parent=None, children=None):
        super(Mul, self).__init__(nums)
        self.name = super(Mul, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children
    
    def __str__(self):
        return self.render_cpp()


class BaseSum:
    
    def __init__(self, nums):
        self.nums = nums
    
    def render_cpp(self):
        code = "("
        for i, n in enumerate(self.nums):
            if i > 0:
                code += "+(" + str(n) + ")"
            else:
                code += str(n)
        code += ")"
        return code


class Sum(BaseSum, NodeMixin):
    def __init__(self, nums, parent=None, children=None):
        super(Sum, self).__init__(nums)
        self.name = super(Sum, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children
    
    def __str__(self):
        return self.render_cpp()
            

class BaseSub:
    
    def __init__(self, nums):
        self.nums = nums
    
    def render_cpp(self):
        code = "("
        for i, n in enumerate(self.nums):
            if i > 0:
                code += "-(" + str(n) + ")"
            else:
                code += str(n)
        code += ")"
        return code


class Sub(BaseSub, NodeMixin):
    def __init__(self, nums, parent=None, children=None):
        super(Sub, self).__init__(nums)
        self.name = super(Sub, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children   
    
    def __str__(self):
        return self.render_cpp()         


class BaseDiv:
    
    def __init__(self, nums, ndiv):
        self.nums = nums
        self.ndiv = ndiv
    
    def render_cpp(self):
        code_line = ""
        # print("self.ndiv {}".format(self.ndiv))
        # print(self.nums)

        if len(self.nums) == 0:
            return "1"

        if self.ndiv > 2:
            code_line = "(("
            for idx, num in enumerate(self.nums):
                
                    if idx < self.ndiv-1:
                        if idx > 0:
                            code_line += "+"
                        code_line += "({})".format(str(num))
                    elif idx == self.ndiv:
                        code_line += "+({}))/(".format(str(num))
                    else:
                        if idx > self.ndiv+1:
                            code_line += "+"
                        code_line += "({})".format(str(num))
            code_line + "))"
        else:
            code_line = "({}/{})".format(str(self.nums[0]), str(self.nums[1]))
        return code_line
        # return "({})/({})".format(str(self.num), str(self.den) if self.den != 0 else 1)


class Div(BaseDiv, NodeMixin):
    # ndiv stands from which number divide
    def __init__(self, nums, ndiv=2, parent=None, children=None):
        super(Div, self).__init__(nums, ndiv)
        self.name = super(Div, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children
    
    def __str__(self):
        return self.render_cpp()