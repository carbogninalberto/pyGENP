import os
import sys
from anytree import Node, RenderTree, PostOrderIter, PreOrderIter, NodeMixin
from anytree.exporter import DotExporter
from utils.operators import Assignment, IfThenElse, WildcardCode, Termination
import generators.tree as gentree


if __name__ == "__main__":
    print("LIBRARY TEST")

    individual = gentree.generate_individual_from_seed()

    DotExporter(individual.root).to_picture("root.png")

    lines = individual.render_code()

    with open(os.path.join(sys.path[0], "prova.cc"), 'w') as f:
        f.writelines(lines)
    f.close()

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

    
    