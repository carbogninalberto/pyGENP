import numpy as np
import random, string
import random_name_generator as rng
import random, string
import uuid

from anytree import Node, PreOrderIter

from core.individual import Individual
from core.types import DefaultConfig, Types
from core.registers import Variable, OperatorRegistry, VariableRegistry
from utils.operators import Assignment, WildcardCode, Equality, \
    IfThenElse, Termination, Mul, Sum, Sub, Div

'''
Append to every node the registry of suitable variables, where in the sub registry are also included
variable found elsewhere
'''


def rand_int(start, end):
    # return int(quantumrandom.randint(start, end))
    # return np.random.randint(start, end)
    return random.randint(start, end-1)

def generate_operator_node(
                            parent_node,
                            max_depth=10,
                            max_width=10,
                            max_branch_depth=3,
                            variables=VariableRegistry([]),
                            wildcard_codes=[],
                            equality_operators=DefaultConfig.EQUALITY,
                            alpha_var_gen=15.0,
                            value_bottom=-100,
                            value_upper=100
                        ):
    ops = DefaultConfig.OPERATORS
    node = None
    if generate_new_variable(alpha_var_gen):
        # generate new varianlr name
        var_name = generate_var_name(variables.variables_name())
        # generate a random expression by using Variables and Operator Registry
        exp = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)
        # generate a new variable
        var = Variable(var_name, Types.get_all()[rand_int(0, len(Types.get_all()))], scope=0)
        # add variable to registry
        variables.register(var)
        # generate an assignment
        node = Assignment(var, exp, parent=parent_node)
    else:
        # random operator
        op_keys = list(DefaultConfig.OPERATORS.keys())
        rand_operator = op_keys[rand_int(0, len(op_keys))]

        if isinstance(ops[rand_operator](), IfThenElse):
            condition = generate_condition(equality_operators, variables)

            exp_t = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)
            exp_f = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)                      

            if len(variables.variables) > 0:
                # some vars in the register 
                tmp_vars = variables.get_random_var()
                var_t = tmp_vars[rand_int(0, len(tmp_vars))] if isinstance(tmp_vars, list) else tmp_vars
                var_f = tmp_vars[rand_int(0, len(tmp_vars))] if isinstance(tmp_vars, list) else tmp_vars

                var_t.recall += 1
                var_f.recall += 1

                var_t_node = Assignment(var_t, exp_t, declare=False)
                var_f_node = Assignment(var_f, exp_f, declare=False)
                
                last_node_t = var_t_node
                last_node_f = var_f_node

                for j in range(rand_int(0, max_branch_depth)):

                    # true branch subtree                        
                    if do_it(y_prob=33.33):
                        rand_code = rand_int(0, len(wildcard_codes))
                        var_t_node_tmp = ops['wildcardCode'](code=wildcard_codes[rand_code], parent=last_node_t)
                        last_node_t = var_t_node_tmp
                    # elif do_it(y_prob=33.33): generate if then else
                    else:
                        tmp_vars_tmp = variables.get_random_var()
                        var_t_tmp = tmp_vars_tmp[rand_int(0, len(tmp_vars_tmp))] if isinstance(tmp_vars_tmp, list) else tmp_vars_tmp
                        var_t_tmp.recall += 1
                        node_exp_t = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)
                        var_t_node_tmp = Assignment(var_t_tmp, node_exp_t, declare=False)
                        var_t_node_tmp.parent = last_node_t
                        # last_node_t.children = var_t_node
                        last_node_t = var_t_node_tmp
                
                for j in range(rand_int(0, max_branch_depth)):
                    # false branch subtree
                    if do_it(y_prob=33.33):
                        rand_code = rand_int(0, len(wildcard_codes))
                        var_f_node_tmp = ops['wildcardCode'](code=wildcard_codes[rand_code], parent=last_node_f)
                        last_node_f = var_f_node_tmp
                    else:
                        tmp_vars_tmp = variables.get_random_var()

                        var_f_tmp = tmp_vars_tmp[rand_int(0, len(tmp_vars_tmp))] if isinstance(tmp_vars_tmp, list) else tmp_vars_tmp
                        var_f_tmp.recall += 1
                        node_exp_f = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)
                        var_f_node_tmp = Assignment(var_f_tmp, node_exp_f, declare=False)
                        var_f_node_tmp.parent = last_node_f   
                        last_node_f = var_f_node_tmp

                node = ops[rand_operator](condition, var_t_node, var_f_node, parent=parent_node)

            else:
                # empty register 
                var_t_name = generate_var_name(variables.variables_name())
                var_t = Variable(var_t_name, Types.get_all()[rand_int(0, len(Types.get_all()))])
                variables.register(var_t)

                var_f_name = generate_var_name(variables.variables_name())
                var_f = Variable(var_f_name, Types.get_all()[rand_int(0, len(Types.get_all()))])
                variables.register(var_f)

                var_t_node = Assignment(var_t, exp_t, declare=True)
                var_f_node = Assignment(var_f, exp_f, declare=True) # , parent=parent_node
                
                node = ops[rand_operator](condition, var_t_node, var_f_node, parent=parent_node)

        elif isinstance(ops[rand_operator](), Assignment):
            # generate expression
            # choose valid var
            if len(variables.variables) > 0:
                tmp_vars = variables.get_random_var()
                var = tmp_vars[rand_int(1, len(tmp_vars))] if isinstance(tmp_vars, list) else tmp_vars
                var.recall += 1

                exp = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)

                # update of existing variable
                node = ops[rand_operator](var, exp, declare=False, parent=parent_node)
            else:                    
                # generate a new variable
                var_name = generate_var_name(variables.variables_name())
                var = Variable(var_name, Types.get_all()[rand_int(1, len(Types.get_all()))], scope=0)            
                # add variable to registry
                variables.register(var)
                exp = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)
                node = ops[rand_operator](var, exp, parent=parent_node)

        elif isinstance(ops[rand_operator](), WildcardCode):
            rand_code = rand_int(0, len(wildcard_codes))
            node = ops[rand_operator](code=wildcard_codes[rand_code], parent=parent_node)
    return node

def generate_individual_from_seed(
                                    seed=42422019,
                                    max_depth=10,
                                    max_width=10,
                                    max_branch_depth=3,
                                    operators=OperatorRegistry(DefaultConfig.OPERATORS),
                                    variables=VariableRegistry([]),
                                    wildcard_codes=['cout << "OK" << endl;'],
                                    equality_operators=DefaultConfig.EQUALITY,
                                    alpha_var_gen=15.0,
                                    value_bottom=-100,
                                    value_upper=100
                                    ):
    '''
    this function generate a tree individual 
    '''
    
    # random.seed(seed)#int(quantumrandom.randint(0, 999999999)))

    # create root node
    root = Node("main")    

    # generate random number of code instruction
    rand_width = rand_int(5, max_width)

    # queue nodes that require validity check to be approved
    pending_nodes = [root]

    # TODO: get configuration in another way
    ops = DefaultConfig.OPERATORS

    # iterate over the decided number of code instructions
    for i in range(rand_width):
        # try to generate a new variable with probability alpha_var_gen
        if generate_new_variable(alpha_var_gen):
            # generate new varianlr name
            var_name = generate_var_name(variables.variables_name())
            # generate a random expression by using Variables and Operator Registry
            exp = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)
            # generate a new variable
            var = Variable(var_name, Types.get_all()[rand_int(0, len(Types.get_all()))], scope=i)
            # add variable to registry
            variables.register(var)
            # generate an assignment
            var_node = Assignment(var, exp, parent=pending_nodes[i])

            #print("\t -> name: {} | exp: {}".format(var_name, exp))

            # add new created node to queue for validation
            pending_nodes.append(var_node)
        else:
            # random operator
            op_keys = list(DefaultConfig.OPERATORS.keys())
            rand_operator = op_keys[rand_int(0, len(op_keys))]

            if isinstance(ops[rand_operator](), IfThenElse):
                # generate condition
                # generate branch1 (assignment) -> TODO: subtree generation
                # generate branch2 (assignment) -> TODO: subtree generation
                condition = generate_condition(equality_operators, variables)

                exp_t = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)
                exp_f = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)                      

                if len(variables.variables) > 0:
                    # some vars in the register 
                    tmp_vars = variables.get_random_var()
                    var_t = tmp_vars[rand_int(0, len(tmp_vars))] if isinstance(tmp_vars, list) else tmp_vars
                    var_f = tmp_vars[rand_int(0, len(tmp_vars))] if isinstance(tmp_vars, list) else tmp_vars

                    var_t.recall += 1
                    var_f.recall += 1

                    var_t_node = Assignment(var_t, exp_t, declare=False)
                    var_f_node = Assignment(var_f, exp_f, declare=False)
                    
                    last_node_t = var_t_node
                    last_node_f = var_f_node

                    for j in range(rand_int(0, max_branch_depth)):

                        # true branch subtree                        
                        if do_it(y_prob=33.33):
                            rand_code = rand_int(0, len(wildcard_codes))
                            var_t_node_tmp = ops['wildcardCode'](code=wildcard_codes[rand_code], parent=last_node_t)
                            last_node_t = var_t_node_tmp
                        # elif do_it(y_prob=33.33): generate if then else
                        else:
                            tmp_vars_tmp = variables.get_random_var()
                            var_t_tmp = tmp_vars_tmp[rand_int(0, len(tmp_vars_tmp))] if isinstance(tmp_vars_tmp, list) else tmp_vars_tmp
                            var_t_tmp.recall += 1
                            node_exp_t = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)
                            var_t_node_tmp = Assignment(var_t_tmp, node_exp_t, declare=False)
                            var_t_node_tmp.parent = last_node_t
                            # last_node_t.children = var_t_node
                            last_node_t = var_t_node_tmp
                    
                    for j in range(rand_int(0, max_branch_depth)):
                        # false branch subtree
                        if do_it(y_prob=33.33):
                            rand_code = rand_int(0, len(wildcard_codes))
                            var_f_node_tmp = ops['wildcardCode'](code=wildcard_codes[rand_code], parent=last_node_f)
                            last_node_f = var_f_node_tmp
                        else:
                            tmp_vars_tmp = variables.get_random_var()

                            var_f_tmp = tmp_vars_tmp[rand_int(0, len(tmp_vars_tmp))] if isinstance(tmp_vars_tmp, list) else tmp_vars_tmp
                            var_f_tmp.recall += 1
                            node_exp_f = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)
                            var_f_node_tmp = Assignment(var_f_tmp, node_exp_f, declare=False)
                            var_f_node_tmp.parent = last_node_f   
                            last_node_f = var_f_node_tmp

                    # print("ops {} rand_operator {} pending_nodes {} <- getting {} index".format(ops, rand_operator, len(pending_nodes), i))
                    node = ops[rand_operator](condition, var_t_node, var_f_node, parent=pending_nodes[i])
                    #node.type = eq_type
                    pending_nodes.append(node)
                else:
                    # empty register 
                    var_t_name = generate_var_name(variables.variables_name())
                    var_t = Variable(var_t_name, Types.get_all()[rand_int(0, len(Types.get_all()))])
                    variables.register(var_t)

                    var_f_name = generate_var_name(variables.variables_name())
                    var_f = Variable(var_f_name, Types.get_all()[rand_int(0, len(Types.get_all()))])
                    variables.register(var_f)

                    var_t_node = Assignment(var_t, exp_t, declare=True)
                    var_f_node = Assignment(var_f, exp_f, declare=True) # , parent=pending_nodes[i]
                    
                    node = ops[rand_operator](condition, var_t_node, var_f_node, parent=pending_nodes[i])
                    
                    pending_nodes.append(node)

            elif isinstance(ops[rand_operator](), Assignment):
                # generate expression
                # choose valid var
                if len(variables.variables) > 0:
                    tmp_vars = variables.get_random_var()
                    var = tmp_vars[rand_int(1, len(tmp_vars))] if isinstance(tmp_vars, list) else tmp_vars
                    var.recall += 1

                    exp = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)

                    # update of existing variable
                    node = ops[rand_operator](var, exp, declare=False, parent=pending_nodes[i])
                    pending_nodes.append(node)
                else:                    
                    # generate a new variable
                    var_name = generate_var_name(variables.variables_name())
                    var = Variable(var_name, Types.get_all()[rand_int(1, len(Types.get_all()))], scope=i)            
                    # add variable to registry
                    variables.register(var)
                    exp = generate_random_expression(variables, max_depth=max_depth, max_width=max_width, value_bottom=value_bottom, value_upper=value_upper)
                    node = ops[rand_operator](var, exp, parent=pending_nodes[i])
            
                    pending_nodes.append(node)

            elif isinstance(ops[rand_operator](), WildcardCode):
                rand_code = rand_int(0, len(wildcard_codes))
                node = ops[rand_operator](code=wildcard_codes[rand_code], parent=pending_nodes[i])

                pending_nodes.append(node)
    
    individual = Individual(
                            root, 
                            variables, 
                            max_depth=max_depth, 
                            max_width=max_width, 
                            value_bottom=value_bottom,
                            value_upper=value_upper
                        )
    individual.id = uuid.uuid4().hex

    return individual

def take_care_of_individual_termination(root, variables: VariableRegistry, operators, equality_operators, value_bottom=-100, value_upper=100):
    '''
    this function appends termination Nodes () to a certain parent node.
    '''
    if isinstance(root, IfThenElse):
        root.condition = generate_condition(equality_operators, variables)
        root.exp_t = generate_random_expression(variables, value_bottom=value_bottom, value_upper=value_upper)
        root.exp_f = generate_random_expression(variables, value_bottom=value_bottom, value_upper=value_upper)
    elif isinstance(root, Assignment):
        root.var = variables.get_random_var()
        root.var.recall += 1
        root.exp = generate_random_expression(variables, value_bottom=value_bottom, value_upper=value_upper)
    else:
        raise Exception("Unknown Operator {}".format(type(root)))


def generate_condition(equality_operators, variables: VariableRegistry):
    # operator generation
    eq_type = list(equality_operators.values())[rand_int(0, len(equality_operators.values()))]
    lf = variables.get_random_var()
    rg = variables.get_random_var()
    
    # now only boolean -> to implement other kinds
    #return Equality(lf="true") if np.random.randint(0, 1001) > 500 else Equality(lf="false")
    return Equality(lf=lf, rg=rg, tp=eq_type)

def create_random_op(op_id):
    '''
    this function instantiate a empty operation node
    '''
    # generate new operator with empty values
    op_keys = list(DefaultConfig.MATH_OPERATORS.keys())
    key = op_keys[op_id]

    ops = DefaultConfig.MATH_OPERATORS
    return ops[key], key


def generate_random_expression(variables, operators=DefaultConfig.MATH_OPERATORS, max_depth=10, max_width=10, value_bottom=-100, value_upper=100):
    '''
    this function generates a random expression tree using variables
    '''
    # having random depth generate tree with expression and termination points (constants)
    rand_op_id = rand_int(0, len(operators.keys()))
    root_op, root_key = create_random_op(rand_op_id)
    root = root_op([])

    pending_nodes = [root]

    if not generate_termination(y_prob=20):
        # take operator as root
        
        rand_op_id = rand_int(0, len(operators))
        op, key = create_random_op(rand_op_id)

        node = op([])
        rand_depth = rand_int(1, max_depth)

        pending_nodes.append(node)
        tmp_nodes = [node]
        
        for j in range(rand_depth):
            rand_op_id = rand_int(0, len(operators))
            sub_op, sub_key = create_random_op(rand_op_id)
            sub_node = sub_op([])

            tmp_nodes.append(sub_node)
            pending_nodes.append(sub_node)

        # adding termination
        for i in range(len(pending_nodes)):
            take_care_of_termination(pending_nodes[i], variables, width=max_width, value_bottom=value_bottom, value_upper=value_upper)

    else:
        take_care_of_termination(root, variables, width=max_width, value_bottom=value_bottom, value_upper=value_upper)
    return root


def take_care_of_termination(root, variables, width=5, must_terminate=False, value_bottom=-100, value_upper=100):
    '''
    this function appends termination Nodes (constants or variables) to a certain expression parent node.
    '''

    operators = DefaultConfig.MATH_OPERATORS
    # print("MUL: {} SUM: {} SUB: {} DIV: {}".format(isinstance(root, Mul), isinstance(root, Sum), isinstance(root, Sub), isinstance(root, Div)))
    if isinstance(root, Mul) or \
        isinstance(root, Sum) or \
        isinstance(root, Sub) or \
        must_terminate: # case is Div
        for i in range(rand_int(2, width)):            
            # print("ok")
            use, var = use_variable(variables)

            children = [child for child in root.children] if root.children is not None else []
            # can broke
            if use and var is not None:
                children.append(Termination(var.name, var.tp))
            else:
                generated_number = round(random.uniform(value_bottom, value_upper), 3)
                if generated_number < 0.1:
                    generated_number *= -1
                if generated_number == 0:
                    generated_number = 0.1
                children.append(Termination(generated_number, Types.float))
            
            root.children = children
            root.nums = children

    elif isinstance(root, Div):
        total = rand_int(2, width)
        ndiv = rand_int(1, total-1) if total > 2 else 1
        root.ndiv = ndiv
        for i in range(total):
            use, var = use_variable(variables)

            children = [child for child in root.children] if root.children is not None else []
            if use and var is not None and i < ndiv:
                rand_op_id = rand_int(0, len(operators)-1) # TODO: replace -1 with div replace, it just assumes that the last operator is div
                sub_op, sub_key = create_random_op(rand_op_id)
                sub_node = sub_op([])
                take_care_of_termination(sub_node, variables, width=width, must_terminate=True, value_bottom=value_bottom, value_upper=value_upper)
                children.append(sub_node)
            else:
                val = round(random.uniform(value_bottom, value_upper), 3)
                children.append(Termination(val if int(val) > 0 else 0.1, Types.float))
            root.children = children
            root.nums = children
        # root.num = children[0]
        # root.den = children[1]

        # print("root.ndiv {} | root.nums {}".format(root.ndiv, root.nums))
    else:
        raise Exception("Unknown Math Operator {}".format(type(root)))


def generate_termination(y_prob=80.0):
    '''
    Bernoulli Probability Distribution
    ''' 
    return True if rand_int(0, 1000) < y_prob*10 else False 


def generate_new_variable(y_prob=20.0):
    '''
    Bernoulli Probability Distribution
    '''
    return True if rand_int(0, 1000) < y_prob*10 else False

def do_it(y_prob=50.0):
    return True if rand_int(0, 1000) < y_prob*10 else False

def use_variable(variables, y_prob=20.0, types=Types.get_all()):
    '''
    this function takes as input a <variables> array (from the VariablesRegistry) and a probability 
    of generating a new variable <y_prob>
    '''
    use_variable = True if rand_int(0, 1000) < y_prob*10 else False
    var = None
    found_compatible = False
    if use_variable:
        while not found_compatible and len(variables.variables) > 0 and variables.is_there_compatible(types):
            var = variables.get_random_var()
            var.recall += 1
            if var is not None and var.tp in types:
                found_compatible = True
    return use_variable, var


def generate_var_name(variables, length=10):
    '''
    this function generate a random name
    '''
    alphabet = string.ascii_lowercase
    while True:
        var_name = ''.join(random.choices(string.ascii_letters, k=16)) #''.join(random.choice(alphabet) for i in range(length))
        if var_name not in variables:
           return var_name


