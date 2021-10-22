from .types import DefaultConfig
import secrets
import os
import sys
import random
import subprocess
from anytree import search
import copy
import numpy as np
from utils.operators import IfThenElse, Assignment, Termination
from generators.tree import generate_random_expression
from utils.fitness import tcp_variant_fitness_write_switch
from multiprocessing.pool import ThreadPool as Pool
from anytree import PreOrderIter
import time
from dotenv import load_dotenv
from numba import jit

load_dotenv()

BASE_NS3_PATH = os.getenv('BASE_NS3_PATH')
CPUS = os.getenv('CPUS')

pool_size = int(CPUS)

class Incubator:

    def __init__(
                    self,
                    config=DefaultConfig,
                    variables=None,
                    pop_size=2,
                    generations=20,
                    alfa_var_gen=12.0,
                    const_termination_range=[-20, 20],
                    fitness=None,
                    generator=generate_random_expression
                ):
        
        self.DefaultConfig = DefaultConfig
        self.pop_size = pop_size
        self.generations = generations
        self.population = []
        self.fitness = fitness
        self.variables = variables
        self.current_generation = 1
        self.hall_of_fame = []
        self.generator = generator
    
    # @jit
    def init_population(self, generator):
        for i in range(self.pop_size):
            variables = copy.deepcopy(self.variables)
            # self.population.append(generator.generate_individual_from_seed(variables=variables))
            indiv = generator.generate_individual_from_seed(variables=variables)
            indiv.id = i
            self.population.append(indiv)

    # @jit
    def calculate_fitness(self):
        codes = []
        for idx, individual in enumerate(self.population):
            codes.append(individual.render_code())
        
        #print("codes", codes)

        switch_case_lines = []
        for idx, code in enumerate(codes):
            switch_case_lines.append("case {}:\n{{".format(idx))
            
            for line in code:
                switch_case_lines.append(line)

            switch_case_lines.append("\n\tbreak;}")

        #print("switch", switch_case_lines)

        tcp_variant_fitness_write_switch(switch_case_lines)

        os.chdir(BASE_NS3_PATH)

        configure_command = 'CXXFLAGS="-Wno-error -Wno-unused-variable" ./waf configure --disable-python'
        build_command = 'CXXFLAGS="-Wno-error -Wno-unused-variable" ./waf build'

        try:
            print('configuring...')
            start = time.time()
            out = subprocess.check_output(configure_command, shell=True, timeout=20)
            end = time.time()
            print("configured in {:.3f} seconds".format(end - start))

            print('building...')
            start = time.time()
            try:
                out = subprocess.check_output(build_command, shell=True, timeout=120)
            except Exception as e:
                print("IMPOSSIBLE TO BUILD", e)
            end = time.time()
            print("built in {:.3f} seconds".format(end - start))
        except:
            print('error on configuring or building...')
        
        # print("calculating fitness...")
        #print("[{}] has fitness {}".format(0, self.population[0].max_fitness(0, self.fitness)))

        pool = Pool(pool_size)

        for idx, individual in enumerate(self.population):
            pool.apply_async(self.multiprocessing_fitness, (idx, individual))   

        pool.close()
        pool.join()

    def multiprocessing_fitness(self, idx, individual):
        #for idx, individual in enumerate(self.population):
            # print(">>>>>>>>>>>FITNESS>>>>>>>>>>>")
        # print("[{}] calculating...".format(idx))
        start = time.time()
        print("[{}] has fitness {:.2f}".format(idx, individual.max_fitness(idx, self.fitness)), end='')        
        end = time.time()
        print(" calculated in {:.3f} seconds".format(end - start))

    # @jit
    def tournament_selection(self, k=35, s=15):
        '''
        modified implementation of tournament selection as described in the referenced link.
        ref: https://en.wikipedia.org/wiki/Tournament_selection
        s is the number of selected individual from the tournament to perform crossover
        '''
        # selected individuals
        selected_individuals = []
        # pick k random individuals
        while len(selected_individuals) < k:
            # picking random individual
            indiv = self.population[secrets.randbelow(self.pop_size)]
            # check if already picked
            if indiv in selected_individuals: continue
            # append individual
            selected_individuals.append(indiv)

        best_individuals = []
        min_fitness_individual, max_fitness_individual = self.find_min_max_fitness(selected_individuals)
        # max_fitness_individual = None
        # find the best s individuals
        for idx, individual in enumerate(selected_individuals):
            if len(best_individuals) >= s \
                and individual.fitness > min_fitness_individual.fitness:

                best_individuals = [i for i in best_individuals if i != min_fitness_individual]
                min_fitness_individual, _ = self.find_min_max_fitness(best_individuals)
                continue
            
            if len(best_individuals) < s:
                if individual.fitness > min_fitness_individual.fitness:
                    min_fitness_individual = individual

                elif individual.fitness >= max_fitness_individual.fitness:
                    max_fitness_individual = individual

                best_individuals.append(individual)
        result = [ind for ind in best_individuals if ind.fitness > 5.0]
        return result if len(result) else best_individuals

    # @jit
    def find_min_max_fitness(self, individuals):
        min_fitness = min(individual.fitness for individual in individuals)
        max_fitness = max(individual.fitness for individual in individuals)
        min_individual = [individual for individual in individuals if individual.fitness == min_fitness][0]
        max_individual = [individual for individual in individuals if individual.fitness == max_fitness][0]
        return min_individual, max_individual

    # @jit
    def take_snapshot(self):
        path_folder = os.path.join(sys.path[0], "snapshots", "{}_gen".format(self.current_generation))
        path_file = "{}.cc"

        # assure folder existence
        if not os.path.exists(path_folder):
            os.makedirs(path_folder)
        
        for idx, individual in enumerate(self.population):
            print("snapshot", path_folder + "/" + path_file.format(idx))
            individual.save_to_file(folder=path_folder, file=path_file.format(idx))

    def add_hall_of_fame(self):
        self.population.sort(key=lambda x:x.fitness, reverse=True)
        if int(self.population[0].fitness) > 0: 
            self.hall_of_fame.append({"id": self.population[0].id, "fitness": self.population[0].fitness, "gen": self.current_generation})

    # @jit
    def crossover(self, best_individuals):
        # count how many offsprings to generate
        offsprings = self.DefaultConfig.TOURNAMENT['k'] - len(best_individuals)
        print("offsprings to generate are {}".format(offsprings))
        # reset population to best individuals
        self.population = best_individuals
        # create parent pool set
        parent_pool = set(best_individuals)
        counter_idx = len(self.population)+1
        # generate new offsprings by
        while len(self.population) < self.pop_size:
            variables = copy.deepcopy(self.variables)
            # self.population.append(generator.generate_individual_from_seed(variables=variables))
            indiv = self.generator(variables=variables)
            indiv.id = counter_idx
            counter_idx += 1

            # pick 2 random parents
            parents = random.sample(parent_pool, 1)
            # convert nodes to sets
            parent_one_nodes = set(parents[0].root.children)
            parent_two_nodes = set(indiv.root.children)
            # parent_two_nodes = search.findall(parents[1].root)
            # init new individual
            child = copy.deepcopy(parents[0])
            # child = copy.deepcopy(indiv)
            # pick random part of the tree
            if len(parent_one_nodes) > 1:
                subtree_one = copy.deepcopy(random.sample(parent_one_nodes, 1)[0])
                # perform crossover
                # first operation
                first_child_branch = random.sample(child.root.children, 1)[0]
                first_child_branch.children = []
                subtree_one.parent = first_child_branch

            if len(parent_two_nodes) > 1:
                subtree_two = copy.deepcopy(random.sample(parent_two_nodes, 1)[0])
                # perform crossover            
                # second operation
                second_child_branch = random.sample(indiv.root.children, 1)[0]
                second_child_branch.children = []
                subtree_two.parent = second_child_branch
            
            # updating variables
            child.update_variable_registry(generate_random_expression)

            # add child to population
            self.population.append(child)
            # indiv.children.append(child)
            # child.parent = indiv
            # self.population.append(indiv)

    def fix_not_valid_crossover(self):
        for idx, ind in enumerate(self.population):
            lines = []
            exclude = True
            seen_variables = [v for v in self.variables.variables_name()]
            already_declared = []
            last_node = None
            looking_nested_if = False
            for node in PreOrderIter(ind.root):
                # if isinstance(node, Assignment) and node.var.name not in seen_variables and node.declare == True and node.parent == ind.root:
                if isinstance(node, Assignment) and node.declare == True:
                    if node.var in already_declared:
                        children = node.parent.children
                        node.parent.children = []
                        for child in children:
                            if not isinstance(child, Assignment) and child.var.name == node.var.name:
                                node.parent.children.append(child)
                    else:
                        already_declared.append(node.var)
                    # seen_variables.append(node.var.name)

                    
                if True: #not exclude:
                    if isinstance(node, Termination) and node.value not in seen_variables: 
                        if node.parent is not None:
                            node.parent.children = []

                        # print("NODEVALUE", node.value)
                        # # random_var_idx = np.random.randint(0, len(seen_variables))
                        # node.value = 1 # seen_variables[random_var_idx]
                    if isinstance(node, IfThenElse):
                        node.parent.children = []

                        # if isinstance(node.exp_t, Assignment) and node.exp_t.var.name not in seen_variables and node.exp_t.declare == False:
                        #     node.exp_t = 'std::cout << "true";' 
                        # if isinstance(node.exp_f, Assignment) and node.exp_f.var.name not in seen_variables and node.exp_f.declare == False:
                        #     node.exp_f = 'std::cout << "false";'

                    if isinstance(node, Assignment) and node.var.name not in seen_variables and node.declare == False: 

                        if node.parent is not None:
                            node.parent.children = []


                        # node.declare = True
                        # if not isinstance(node.parent, IfThenElse):
                        #     seen_variables.append(node.var.name)


                        
                        # children = node.parent.children
                        # node.parent.children = []
                        # for child in children:
                        #     if not isinstance(child, Assignment) and child.var.name == node.var.name:
                        #         node.parent.children.append(child)
                        
                        # node.declare = True
                        # for child in node.children:
                            # child.parent = node.parent
                    if isinstance(node, Assignment) and node.var.name in seen_variables and node.declare == True: 
                        if node.parent is not None:
                            node.parent.children = []
                        # node.declare = False
                else:
                    exclude = False

    def mutate(self, y_prob=50.0):
        return True if np.random.randint(0, 1000) < y_prob*10 else False 

    # @jit
    def mutation(self):
        for idx, individual in enumerate(self.population):
            if self.mutate():
                # operator flipping
                if (len(individual.root.children) >= 1):
                    random_node = random.sample(individual.root.children, 1)[0]
                    # random operator
                    if isinstance(random_node, IfThenElse):
                        tmp_vars = individual.variables.get_random_var()
                        var_t = tmp_vars[np.random.randint(0, len(tmp_vars))] if isinstance(tmp_vars, list) else tmp_vars
                        var_f = tmp_vars[np.random.randint(0, len(tmp_vars))] if isinstance(tmp_vars, list) else tmp_vars

                        var_t.recall += 1
                        var_f.recall += 1
                        
                        exp_t = generate_random_expression(individual.variables)
                        exp_f = generate_random_expression(individual.variables)  

                        random_node.exp_t = Assignment(var_t, exp_t, declare=False)
                        random_node.exp_f = Assignment(var_f, exp_f, declare=False)
                    elif isinstance(random_node, Assignment):
                        random_node.exp = generate_random_expression(individual.variables)

    def run(self, generator):
        # init population giving a generator
        self.init_population(generator)

        for i in range(self.generations):
            # take snapshot of generated individuals
            self.take_snapshot()

            #self.mutation()

            #break

            self.calculate_fitness()

            self.add_hall_of_fame()

            print("[GENERATION {}/{}] with population:".format(self.current_generation, self.pop_size))
            print("[GENERATION {}/{}] HALL OF FAME: {}".format(self.current_generation, self.pop_size, [str(ind) for ind in self.hall_of_fame]))

            for idx, ind in enumerate(self.population):
                print("id:{}, fitness:{:.2f}, variables: {}".format(idx,ind.fitness, ind.variables))

            selected = self.tournament_selection(
                k=self.DefaultConfig.TOURNAMENT["k"],
                s=self.DefaultConfig.TOURNAMENT["s"])

            print("{} SELECTED INDIVIDUALS".format(len(selected)))


            for idx, ind in enumerate(selected):
                print("id:{}, fitness:{:.2f}".format(idx,ind.fitness))

            if len(selected) >= 2:
                self.crossover(selected)
                # self.fix_not_valid_crossover()

            self.mutation()

            if len(selected) == 0:
                print("GOT NOT AVAILABLE INDIVIDUALS")
                self.population = []
                self.init_population()

            self.current_generation += 1

        print("FINAL POPULATION")
        print([ind.fitness for ind in self.population])
        print("HALL OF FAME:")
        print([str(ind) for ind in self.hall_of_fame])



