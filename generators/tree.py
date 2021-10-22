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


def generate_individual_from_seed(
                                    seed=42422019,
                                    max_depth=20,
                                    max_width=20,
                                    operators=OperatorRegistry(DefaultConfig.OPERATORS),
                                    variables=VariableRegistry([]),
                                    equality_operators=DefaultConfig.EQUALITY,
                                    alpha_var_gen=35.0
                                    ):
    '''
    this function generate a tree individual 
    '''

    # create root node
    root = Node("main")    

    # generate random number of code instruction
    rand_width = np.random.randint(1, max_width)

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
            exp = generate_random_expression(variables)
            # generate a new variable    
            var = Variable(var_name, Types.get_all()[np.random.randint(0, len(Types.get_all()))], scope=i)       
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
            rand_operator = op_keys[np.random.randint(0, len(op_keys))]

            if isinstance(ops[rand_operator](), IfThenElse):
                # generate condition
                # generate branch1 (assignment) -> TODO: subtree generation
                # generate branch2 (assignment) -> TODO: subtree generation
                condition = generate_condition(equality_operators, variables)
                exp_t = generate_random_expression(variables)
                exp_f = generate_random_expression(variables)               

                if len(variables.variables) > 0:
                    # some vars in the register 
                    tmp_vars = variables.get_random_var()
                    var_t = tmp_vars[np.random.randint(0, len(tmp_vars))] if isinstance(tmp_vars, list) else tmp_vars
                    var_f = tmp_vars[np.random.randint(0, len(tmp_vars))] if isinstance(tmp_vars, list) else tmp_vars

                    var_t.recall += 1
                    var_f.recall += 1

                    var_t_node = Assignment(var_t, exp_t, declare=False)
                    var_f_node = Assignment(var_f, exp_f, declare=False)

                    node = ops[rand_operator](condition, var_t_node, var_f_node, parent=pending_nodes[i])
                    #node.type = eq_type
                    pending_nodes.append(node)
                else:
                    # empty register 
                    var_t_name = generate_var_name(variables.variables_name())
                    var_t = Variable(var_t_name, Types.get_all()[np.random.randint(0, len(Types.get_all()))])
                    variables.register(var_t)

                    var_f_name = generate_var_name(variables.variables_name())
                    var_f = Variable(var_f_name, Types.get_all()[np.random.randint(0, len(Types.get_all()))])
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
                    var = tmp_vars[np.random.randint(1, len(tmp_vars))] if isinstance(tmp_vars, list) else tmp_vars
                    var.recall += 1

                    exp = generate_random_expression(variables)

                    # update of existing variable
                    node = ops[rand_operator](var, exp, declare=False, parent=pending_nodes[i])
                    pending_nodes.append(node)
                else:                    
                    # generate a new variable
                    var_name = generate_var_name(variables.variables_name())
                    var = Variable(var_name, Types.get_all()[np.random.randint(1, len(Types.get_all()))], scope=i)            
                    # add variable to registry
                    variables.register(var)
                    exp = generate_random_expression(variables)
                    node = ops[rand_operator](var, exp, parent=pending_nodes[i])
            
                    pending_nodes.append(node)

            #print("pending nodes: ", pending_nodes)
            # if isinstance(ops[rand_operator], IfThenElse):
            #     rand_depth = np.random.randint(0, max_depth)
            #     for j in range(rand_depth):
            #         rand_operator = np.random.randint(0, len(operators))
    
    # TODO: take care of termination and validity check
    # for pending_node in pending_nodes[1:]:
    #     print(str(pending_node))
        #take_care_of_individual_termination(pending_node, variables, operators)

    # individual.root = root
    # lines = []
    # for node in PreOrderIter(individual.root):
    #     lines.append(str(node))
    # print(lines)
    # validity check requires => type check and variable scope accessibility
        # generate empty individual
    individual = Individual(root, variables, max_depth=max_depth, max_width=max_width)
    individual.id = uuid.uuid4().hex

    return individual


def take_care_of_individual_termination(root, variables: VariableRegistry, operators, equality_operators):
    '''
    this function appends termination Nodes () to a certain parent node.
    '''
    if isinstance(root, IfThenElse):
        root.condition = generate_condition(equality_operators, variables)
        root.exp_t = generate_random_expression(variables)
        root.exp_f = generate_random_expression(variables)
    elif isinstance(root, Assignment):
        root.var = variables.get_random_var()
        root.var.recall += 1
        root.exp = generate_random_expression(variables)
    else:
        raise Exception("Unknown Operator {}".format(type(root)))


def generate_condition(equality_operators, variables: VariableRegistry):
    # operator generation
    eq_type = list(equality_operators.values())[np.random.randint(0, len(equality_operators.values()))]
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


def generate_random_expression(variables, operators=DefaultConfig.MATH_OPERATORS, max_depth=5, max_width=10):
    '''
    this function generates a random expression tree using variables
    '''
    # having random depth generate tree with expression and termination points (constants)
    rand_op_id = np.random.randint(0, len(operators.keys()))
    root_op, root_key = create_random_op(rand_op_id)
    root = root_op([]) if root_key != 'div' else root_op([], [])

    rand_width = np.random.randint(0, max_width)
    pending_nodes = [root]

    if not generate_termination():
        # take operator as root
        
        rand_op_id = np.random.randint(0, len(operators))
        op, key = create_random_op(rand_op_id)

        node = op([]) if key != 'div' else op([], [])        
        rand_depth = np.random.randint(3, max_depth)

        pending_nodes.append(node)
        tmp_nodes = [node]
        
        for j in range(rand_depth):
            if not generate_termination():
                rand_op_id = np.random.randint(0, len(operators))
                sub_op, sub_key = create_random_op(rand_op_id)
                sub_node = sub_op([]) if sub_key != 'div' else sub_op([], [])

                tmp_nodes.append(sub_node)
                pending_nodes.append(sub_node)
                #pending_nodes.append(node)
            else:
                break
        
        updated_nodes = []
        # adding termination
        for i in range(len(pending_nodes)):
            take_care_of_termination(pending_nodes[i], variables)
        #     n = take_care_of_termination(pending_nodes[i], variables)
        #     if i > 0:
        #         n.parent = pending_nodes[i-1]
        #     updated_nodes.append(n)

    else:
        take_care_of_termination(root, variables)
    return root


def take_care_of_termination(root, variables, width=5):
    '''
    this function appends termination Nodes (constants or variables) to a certain expression parent node.
    '''
    
    if isinstance(root, Mul) or \
        isinstance(root, Sum) or \
        isinstance(root, Sub):
        for i in range(np.random.randint(2, width)):
            use, var = use_variable(variables)

            children = [child for child in root.children] if root.children is not None else []
            # if use and var is not None:
            #     children.append(Termination(var.name, var.tp))
            # else:
            children.append(Termination(np.random.randint(10, 2001)/100.0, Types.float))
            
            root.children = children
            root.nums = children

    elif isinstance(root, Div):
        for i in range(2-len(root.children)):
            use, var = use_variable(variables)

            children = [child for child in root.children] if root.children is not None else []
            # if use and var is not None:
            #     children.append(Termination(var.name, var.tp))
            # else:
            val = np.random.randint(10, 2001)/100.0
            children.append(Termination(val if val != 0 else 1, Types.float))
            root.children = children
        root.num = children[0]
        root.den = children[1]
    else:
        raise Exception("Unknown Math Operator {}".format(type(root)))


def generate_termination(y_prob=30.0):
    '''
    Bernoulli Probability Distribution
    ''' 
    return True if np.random.randint(0, 1000) < y_prob*10 else False 


def generate_new_variable(y_prob=20.0):
    '''
    Bernoulli Probability Distribution
    '''
    return True if np.random.randint(0, 1000) < y_prob*10 else False


def use_variable(variables, y_prob=20.0, types=Types.get_all()):
    '''
    this function takes as input a <variables> array (from the VariablesRegistry) and a probability 
    of generating a new variable <y_prob>
    '''
    use_variable = True if np.random.randint(0, 1000) < y_prob*10 else False
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


