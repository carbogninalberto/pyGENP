from core.individual import Individual
from .types import DefaultConfig
import secrets
import os
import sys
import random
import pickle
import subprocess
from anytree import search
import copy
import json
import numpy as np
from utils.operators import IfThenElse, Assignment, Mul, Sub, Sum, Termination
from generators.tree import generate_random_expression
from utils.fitness import tcp_variant_fitness_write_switch
from multiprocessing.pool import ThreadPool as Pool
from anytree import PreOrderIter
import time
from dotenv import load_dotenv
from numba import jit
from prompt_toolkit import print_formatted_text, HTML

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
                    const_termination_range=[-20, 20],
                    fitness=None,
                    generator=generate_random_expression,
                    max_depth=10,
                    max_width=10,
                    max_branch_depth=3,
                    value_bottom=-100,
                    value_upper=100,
                    alpha_var=35,
                    save_individual=False,
                    max_mutations=10,
                    max_code_lines=100
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
        self.max_depth = max_depth
        self.max_width = max_width
        self.max_branch_depth = max_branch_depth
        self.value_bottom = value_bottom
        self.value_upper = value_upper
        self.alpha_var = alpha_var
        self.save_individual=False
        self.max_mutations = max_mutations
        self.max_code_lines = max_code_lines
        self.current_gen = []
    
    # @jit
    def init_population(self, generator, pickles=[]):
        loaded_pickle = 0
        for idx, p in enumerate(pickles):
            try:
                with open(p, 'rb') as f:
                    indiv = pickle.load(f)
                    indiv.id = idx
                    self.population.append(indiv)
                    loaded_pickle += 1
            except Exception as e:
                print("Cannot load pickle, try next one")
        
        for i in range(self.pop_size-loaded_pickle):
            variables = copy.deepcopy(self.variables)
            # self.population.append(generator.generate_individual_from_seed(variables=variables))
            indiv = generator.generate_individual_from_seed(
                variables=variables, 
                wildcard_codes=self.DefaultConfig.WILD_CARD_CODE,
                max_depth=self.max_depth,
                max_width=self.max_width,
                alpha_var_gen=self.alpha_var,
                value_bottom=self.value_bottom,
                value_upper=self.value_upper
            )
            indiv.id = i + loaded_pickle
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
                out = subprocess.check_output(build_command, shell=True, timeout=240)
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
        fit = individual.max_fitness(idx, self.fitness, self.max_code_lines)
        print("[{}] \thas fitness\t {:.2f}".format(idx, fit), end='')        
        end = time.time()
        print(" calculated in {:.1f} \tseconds".format(end - start))

        self.current_gen.append({
            'gen': self.current_generation,
            'id': idx,
            'fitness': fit,
            'path': "snapshots/{}_gen/{}.cc".format(self.current_generation, idx),
            'time': (end - start)
        })
        
        path_folder_out_gen = os.path.join(sys.path[0], "snapshots")
        path_file_out_gen = "{}/current_gen.json".format(path_folder_out_gen)
        with open(path_file_out_gen, 'w') as out_gen:
            json.dump(self.current_gen, out_gen)

        

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

        path_pickles = os.path.join(sys.path[0], "snapshots_pickles", "{}_gen".format(self.current_generation))
        path_file_pickles = "{}.pickle"

        # assure folder existence
        if not os.path.exists(path_folder):
            os.makedirs(path_folder)
        
        if not os.path.exists(path_pickles):
            os.makedirs(path_pickles)
        
        # output individuals
        
        for idx, individual in enumerate(self.population):
            try:
                # print("snapshot", path_folder + "/" + path_file.format(idx))
                individual.save_to_file(folder=path_folder, file=path_file.format(idx))
            except Exception as e:
                print("not exported individual, but still continuing")
        print_formatted_text(HTML('<aaa fg="black" bg="ansigreen"><b>{} SNAPSHOTS EXPORTED TO: {}</b></aaa>'.format(len(self.population), path_folder)))

        # output pickles
        for idx, individual in enumerate(self.population):
            try:
                # print("pickle", path_pickles + "/" + path_file_pickles.format(idx))
                path = os.path.join(path_pickles, path_file_pickles.format(idx))
                with open(path, 'wb') as f:
                    pickle.dump(individual, f, protocol=pickle.HIGHEST_PROTOCOL)
                f.close()
            except Exception as e:
                print("not exported individual pickle, but still continuing")
        print_formatted_text(HTML('<aaa fg="black" bg="ansigreen"><b>{} PICKLES EXPORTED TO: {}</b></aaa>'.format(len(self.population), path_pickles)))
    
    def add_hall_of_fame(self, add_to_elite=False):
        self.population.sort(key=lambda x:x.fitness, reverse=True)
        if int(self.population[0].fitness) > 0: 
            self.hall_of_fame.append({"id": self.population[0].id, "fitness": self.population[0].fitness, "gen": self.current_generation})
            if add_to_elite == True:
                self.population[0].is_elite = True
            return self.population[0] # return best individual
        return None

    # @jit
    def crossover(self, best_individuals, there_is_elite, elite=None):
        # count how many offsprings to generate
        offsprings = self.DefaultConfig.TOURNAMENT['k'] - len(best_individuals)
        print("offsprings to generate are {}".format(offsprings))
        # reset population to best individuals
        self.population = best_individuals
        # create parent pool set
        parent_pool = set(best_individuals)
        if there_is_elite and elite is not None:
            parent_pool.add(elite)
        counter_idx = len(self.population)+1

        place_for_elite = 1 if there_is_elite else 0

        # generate new offsprings by
        while len(self.population) < self.pop_size-place_for_elite: # -1 because elite individual is added afterwards
            variables = copy.deepcopy(self.variables)
            # self.population.append(generator.generate_individual_from_seed(variables=variables))
            indiv = self.generator(variables=variables, max_depth=self.max_depth, max_width=self.max_width)
            indiv.id = counter_idx
            counter_idx += 1

            # pick 2 random parents
            parents = random.sample(parent_pool, 1)
            # convert nodes to sets
            parent_one_nodes = [n for n in PreOrderIter(parents[0].root.children[0])]
            parent_two_nodes = [n for n in PreOrderIter(indiv.root.children[0])]
            # parent_two_nodes = search.findall(parents[1].root)
            # init new individual
            child = copy.deepcopy(parents[0])
            # child = copy.deepcopy(indiv)
            # pick random part of the tree
            if len(parent_one_nodes) > 1:
                subtree_one = copy.deepcopy(random.sample(parent_one_nodes, 1)[0])
                subtree_one.parent = None
                # perform crossover
                # first operation
                first_child_branch = random.sample([n for n in PreOrderIter(child.root.children[0])], 1)[0]
                # first_child_branch.children = [subtree_one]
                subtree_one.parent = first_child_branch

                # print("--\1/--{}".format(type(first_child_branch)))

            if len(parent_two_nodes) > 1:
                subtree_two = copy.deepcopy(random.sample(parent_two_nodes, 1)[0])
                subtree_two.parent = None
                # perform crossover            
                # second operation
                second_child_branch = random.sample([n for n in PreOrderIter(indiv.root.children[0])], 1)[0]
                # second_child_branch.children = [subtree_two]
                subtree_two.parent = second_child_branch

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

    def mutate_switch_branches(self, y_prob=30):
        return True if np.random.randint(0, 1000) < y_prob*10 else False

    # @jit
    def mutation(self):
        for idx, individual in enumerate(self.population):
            if not isinstance(individual, Individual):
                print("ERROR added something different as individual")
                quit()
            if self.mutate(y_prob=self.DefaultConfig.MUTATION['truncate_node']) and not individual.is_elite:
                # truncate mutation
                nodes = [node for node in PreOrderIter(individual.root)]
                selected_node = nodes[secrets.randbelow(len(nodes))]
                # selected_node.parent.children = []
                selected_node.parent = None
            if self.mutate(y_prob=self.DefaultConfig.MUTATION['operator_flip']) and not individual.is_elite:
                # operator flipping
                if (len(individual.root.children) >= 1):
                    
                    counter = np.random.randint(1, self.max_mutations)
                    while counter > 0:
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
                        counter -= 1
                # switch branches
                if self.mutate_switch_branches(y_prob=self.DefaultConfig.MUTATION['switch_branches']):
                    for node in PreOrderIter(individual.root):
                        if isinstance(node, IfThenElse):
                            tmp = copy.deepcopy(node.exp_f)
                            node.exp_f = copy.deepcopy(node.exp_t)
                            node.exp_t = tmp
                            break
                # switch compatible operators
                # for instance sum with multiplication
                if self.mutate(y_prob=self.DefaultConfig.MUTATION['switch_exp']):
                    for node in PreOrderIter(individual.root):
                        if isinstance(node, Assignment):
                            for oper in PreOrderIter(node.exp):
                                if self.mutate(y_prob=20):
                                    if isinstance(oper, Mul):
                                        new_oper = Sum(oper.nums)
                                        new_oper.parent = oper.parent
                                        for child in new_oper.children:
                                            child.parent = new_oper
                                    elif isinstance(oper, Sum):
                                        new_oper = Mul(oper.nums)
                                        new_oper.parent = oper.parent
                                        for child in new_oper.children:
                                            child.parent = new_oper                                    
                                    elif isinstance(oper, Sub):
                                        new_oper = Mul(oper.nums)
                                        new_oper.parent = oper.parent
                                        for child in new_oper.children:
                                            child.parent = new_oper
                                    break
                        
                            
                    

    def run(self, generator, pickles=[]):
        # init population giving a generator
        self.init_population(generator, pickles)

        for i in range(self.generations):
            # take snapshot of generated individuals
            self.take_snapshot()

            #self.mutation()
            #break

            self.calculate_fitness()

            elite_individual = copy.deepcopy(self.add_hall_of_fame(add_to_elite=True))

            # write out the hall of fame
            path_folder_hall = os.path.join(sys.path[0], "snapshots")
            path_file_hall = "{}/hall_of_fame.json".format(path_folder_hall)
            with open(path_file_hall, 'w') as out_hall:
                json.dump(self.hall_of_fame, out_hall)

            print("[GENERATION {}/{}] with population:".format(self.current_generation, self.pop_size))

            for idx, ind in enumerate(self.population):
                print("id:{}, fitness:{:.2f}, variables: {}".format(idx,ind.fitness, ind.variables.variables_name()))

            selected = self.tournament_selection(
                k=self.DefaultConfig.TOURNAMENT["k"],
                s=self.DefaultConfig.TOURNAMENT["s"])
            
            # print("[GENERATION {}/{}] HALL OF FAME: {}".format(self.current_generation, self.pop_size, [str(ind) for ind in self.hall_of_fame]))
            print_formatted_text(HTML(
                "<aaa fg=\"white\" bg=\"red\"><b>[GENERATION {}/{}] HALL OF FAME: {}</b></aaa>".format(self.current_generation, self.pop_size, [str(ind) for ind in self.hall_of_fame])
            ))


            print("{} SELECTED INDIVIDUALS".format(len(selected)))

            for idx, ind in enumerate(selected):
                print("id:{}, fitness:{:.2f}".format(idx,ind.fitness))

            # self.population = []
            there_is_elite = elite_individual is not None
            if len(selected) >= 2:
                self.crossover(selected, there_is_elite=there_is_elite, elite=elite_individual)
                # self.fix_not_valid_crossover()

            self.mutation()

            
            for ind in self.population:
                # updating variables
                ind.update_variable_registry(generate_random_expression)
            

            if len(selected) == 0:
                print("GOT NOT AVAILABLE INDIVIDUALS")
                self.population = []
                self.init_population(generator, pickles)

            if elite_individual is not None:
                # print("[ELITE INDIVIDUAL] id:{}, fitness:{}".format(elite_individual.id, elite_individual.fitness))
                print_formatted_text(HTML(
                    "<aaa fg=\"black\" bg=\"yellow\"><b>[ELITE INDIVIDUAL] id:{}, fitness:{}</b></aaa>".format(elite_individual.id, elite_individual.fitness)
                ))
                self.population.append(elite_individual)
            
            self.current_generation += 1
            self.current_gen = []

        print("FINAL POPULATION")
        print([ind.fitness for ind in self.population])
        print("HALL OF FAME:")
        print([str(ind) for ind in self.hall_of_fame])

    def kill(self):
        sys.exit()


