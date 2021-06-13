from anytree import NodeMixin


class BaseTermination:

    def __init__(self, value, tp):
        self.value = value
        self.tp

    def render_cpp(self):
        return "{}".format(self.value)
    
    def __str__(self):
        return self.render_cpp()


class Termination(BaseTermination, NodeMixin):

    def __init__(self, value, tp, parent=None, children=None):
        super(Termination, self).__init__(value, tp)
        self.name = super(Termination, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children


class BaseEquality:

    def __init__(self, lf, rg):
        self.lf = lf
        self.rg = rg

    def render_cpp(self):
        return "{} == {}".format(self.lf, self.rg)
    
    def __str__(self):
        return self.render_cpp()


class Equality(BaseEquality, NodeMixin):

    def __init__(self, lf, rg, parent=None, children=None):
        super(Equality, self).__init__(lf, rg)
        self.name = super(Equality, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children


class BaseAssignment:
    
    def __init__(self, var, exp, declare=True):
        self.var = var
        self.exp = exp
        self.declare = declare

    def render_cpp(self):
        return "{}{} = {};\n".format("int " if self.declare else "", self.var, self.exp)

    def __str__(self):
        return self.render_cpp()


class Assignment(BaseAssignment, NodeMixin):

    def __init__(self, var, exp, declare=True, parent=None, children=None):
        super(Assignment, self).__init__(var, exp, declare)
        self.name = super(Assignment, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children


class BaseIfThenElse:

    def __init__(self, condition, exp_true, exp_false):
        self.condition = condition
        self.exp_true = exp_true
        self.exp_false = exp_false
    
    def render_cpp(self):
        return "if({}){{\n\t{}}}\nelse{{\n\t{}\n}}\n".format(self.condition, self.exp_true, self.exp_false)

    def __str__(self):
        return self.render_cpp()


class IfThenElse(BaseIfThenElse, NodeMixin):

    def __init__(self, condition, exp_true, exp_false, parent=None, children=None):
        super(IfThenElse, self).__init__(condition, exp_true, exp_false)
        self.name = super(IfThenElse, self).render_cpp()
        self.parent = parent
        self.children = [self.exp_true, self.exp_false]


class BaseWildcardCode:

    def __init__(self, code):
        self.code = code
    
    def render_cpp(self):
        return self.code
    
    def __str__(self):
        return self.render_cpp()

class WildcardCode(BaseWildcardCode, NodeMixin):

    def __init__(self, code, parent=None, children=None):
        super(WildcardCode, self).__init__(code)
        self.name = super(WildcardCode, self).render_cpp()
        self.parent = parent
        if children:
            self.children = children