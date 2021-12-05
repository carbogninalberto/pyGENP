from multiprocessing import Process
import genp
# from io import StringIO
import sys
import os

# sys.stdout = buffer = StringIO()

class SimThread(Process):
    def __init__(self, pop, gen, k, s, operator_flip, switch_branches, switch_exp, truncate_node):
        super(SimThread, self).__init__()
        self.pop = int(pop)
        self.gen = int(gen)
        self.k = int(k)
        self.s = int(s)
        self.operator_flip = int(operator_flip)
        self.switch_branches = int(switch_branches)
        self.switch_exp = int(switch_exp)
        self.truncate_node = int(truncate_node)
        self.incubator = None
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
            generations=self.gen
        )

        # evolve population
        self.incubator.run(
            generator=genp.tree
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