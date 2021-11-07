import os
import sys
from anytree import Node, RenderTree, PostOrderIter, PreOrderIter, NodeMixin
from anytree.exporter import DotExporter
#from utils.operators import Assignment, IfThenElse, WildcardCode, Termination
#import utils.parser as up
import genp
#import generators.tree as gentree
from numba import jit

TCP_LINUX_RENO_CONGESTION_AVOIDANCE = r"""uint32_t w = tcb->m_cWnd / tcb->m_segmentSize;
if (m_cWndCnt >= w)
{
  m_cWndCnt = 0;
  tcb->m_cWnd += tcb->m_segmentSize;
}

m_cWndCnt += segmentsAcked;
if (m_cWndCnt >= w)
{
  uint32_t delta = m_cWndCnt / w;

  m_cWndCnt -= delta * w;
  tcb->m_cWnd += delta * tcb->m_segmentSize;
}""";


if __name__ == "__main__":

    variables = genp.registers.VariableRegistry([
        genp.registers.Variable("tcb->m_segmentSize", genp.types.Types.integer),
        genp.registers.Variable("tcb->m_cWnd", genp.types.Types.integer),
        genp.registers.Variable("segmentsAcked", genp.types.Types.integer)        
    ])

    custom_config = genp.types.DefaultConfig
    custom_config.TOURNAMENT = {
        "k": 7, # how many individual to randomly select from population 
        "s": 4 # how many to select if minimum fitness requirement is met
    }

    # custom_config.WILD_CARD_CODE = ['//empty line',]

    custom_config.WILD_CARD_CODE = [
        "segmentsAcked = SlowStart (tcb, segmentsAcked);",
        "CongestionAvoidance (tcb, segmentsAcked);",
        "TcpLinuxCongestionAvoidance (tcb, segmentsAcked);"
    ]

    # initialize Incubator
    incubator = genp.Incubator(
        config=custom_config,
        fitness=genp.tcp_variant_fitness_wrapped,
        variables=variables,
        pop_size=7,
        generations=10
    )

    # evolve population
    incubator.run(
        generator=genp.tree
    )

    # numba.cuda.profile_stop()

    

    # init population giving a generator
    # incubator.init_population(genp.tree)

    # take snapshot of generated individuals
    # incubator.take_snapshot()

    # for individual in incubator.population:
    #     print(individual.render_code()[:3])

    # incubator.calculate_fitness()

    # selected = incubator.tournament_selection(k=10, s=3)
    
    # print([s.fitness for s in selected])    

    # incubator.crossover(selected)

    # incubator.current_generation += 1

    # incubator.take_snapshot()

    

    if False:

        individual = genp.tree.generate_individual_from_seed(variables=variables)

        DotExporter(individual.root).to_picture("root.png")

        lines = individual.render_code()

        with open(os.path.join(sys.path[0], "prova.cc"), 'w') as f:
            f.writelines(lines)
        f.close()

        #out = up.parser(file="a.cpp", substitute_lines=lines)
        #up.output_parsed_file(file="a1.cpp", lines=out)

        genp.parser.parser_wrapper(file="examples/tcp/tcp-congestion.cc", lines=lines)

        # print("TEST")

        # root = WildcardCode("int main(){\n")
        # line1 = Assignment("a", "10", parent=root)
        # line2 = IfThenElse("a == 10", Assignment("a", "11", False), Assignment("a", "12", False), parent=root)
        # line3 = Assignment("b", "12", parent=root)
        # end = WildcardCode("}", parent=root)

        # DotExporter(root).to_picture("root.png")

        # lines = render_code(root)

        # with open(os.path.join(sys.path[0], "prova.cc"), 'w') as f:
        #     f.writelines(lines)
        # f.close()

    
    
