from multiprocessing import Process
import genp
# from io import StringIO
import sys
import os

# sys.stdout = buffer = StringIO()

class SimThread(Process):
    def __init__(self, pop, gen, k, s, operator_flip, switch_branches, switch_exp, truncate_node, 
                    max_mutations, value_bottom_limit, value_top_limit, max_code_lines, max_depth, 
                    max_width, alpha_vars, max_branch_depth, payload_size, simulation_time, mtu_bottom_limit, 
                    mtu_upper_limit, mtu_step, pickles):
        super(SimThread, self).__init__()
        self.pop = int(pop)
        self.gen = int(gen)
        self.k = int(k)
        self.s = int(s)
        self.operator_flip = float(operator_flip)
        self.switch_branches = float(switch_branches)
        self.switch_exp = float(switch_exp)
        self.truncate_node = float(truncate_node)
        self.max_mutations = float(max_mutations)
        self.value_bottom_limit = float(value_bottom_limit)
        self.value_top_limit = float(value_top_limit)
        self.max_code_lines = float(max_code_lines)
        self.max_depth = float(max_depth)
        self.max_width = float(max_width)
        self.alpha_vars = float(alpha_vars)
        self.max_branch_depth = float(max_branch_depth)
        self.payload_size = int(payload_size)
        self.simulation_time = int(simulation_time)
        self.mtu_bottom_limit = int(mtu_bottom_limit)
        self.mtu_upper_limit = int(mtu_upper_limit)
        self.mtu_step = int(mtu_step)
        self.incubator = None
        self.pickles = pickles
        self.run_pid = str(os.getpid())
    
    def run(self):
        # self.run_pid = str(os.getpid())
        sys.stdout = open(self.run_pid + ".out", "a", buffering=1)
        sys.stderr = open(self.run_pid + "_error.out", "a", buffering=1)

        variables = genp.registers.VariableRegistry([
            genp.registers.Variable("tcb->m_segmentSize", genp.types.Types.integer),
            genp.registers.Variable("tcb->m_cWnd", genp.types.Types.integer),
            genp.registers.Variable("segmentsAcked", genp.types.Types.integer)        
        ])

        custom_config = genp.types.DefaultConfig
        custom_config.TOURNAMENT = {
            "k": self.k, # how many individual to randomly select from population 
            "s": self.s # how many to select if minimum fitness requirement is met
        }

        custom_config.MUTATION = {
            "operator_flip": self.operator_flip,
            "switch_branches": self.switch_branches,
            "switch_exp": self.switch_exp,
            "truncate_node": self.truncate_node
        }

        # custom_config.WILD_CARD_CODE = ['//empty line',]

        custom_config.WILD_CARD_CODE = [
            "segmentsAcked = SlowStart (tcb, segmentsAcked);",
            "CongestionAvoidance (tcb, segmentsAcked);",
            "TcpLinuxCongestionAvoidance (tcb, segmentsAcked);"
        ]

        # initialize Incubator
        self.incubator = genp.Incubator(
            config=custom_config,
            fitness=genp.tcp_variant_fitness_wrapped,
            variables=variables,
            pop_size=self.pop,
            generations=self.gen,
            max_depth=self.max_depth,
            max_width=self.max_width,
            max_branch_depth=self.max_branch_depth,
            value_bottom=self.value_bottom_limit,
            value_upper=self.value_top_limit,
            alpha_var=self.alpha_vars,
            max_mutations=self.max_mutations,
            max_code_lines=self.max_code_lines
        )

        # evolve population
        self.incubator.run(
            generator=genp.tree,
            pickles=self.pickles
        )

    def get_current_gen(self):
        if self.incubator != None:
            return self.incubator.current_gen
        else:
            return []

    def get_pid(self):
        # print("CALLED")
        # pid = os.getpid()
        # self._stop_event.set()
        # self.incubator.kill()
        # sys.exit()
        return self.run_pid
    
    # def get_log(self):
    #     buffer.getvalue()