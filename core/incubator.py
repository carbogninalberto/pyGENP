from core.individual import Individual
from .types import DefaultConfig
import secrets
import os
import math
import sys
import random
import gc
import pickle
import subprocess
from anytree import search, RenderTree
import copy
import json
import numpy as np
from utils.operators import IfThenElse, Assignment, Mul, Sub, Sum, Termination
from generators.tree import generate_operator_node, generate_random_expression, generate_individual_from_seed
from utils.fitness import tcp_variant_fitness_write_switch
from multiprocessing.pool import ThreadPool as Pool
from anytree import PreOrderIter
import time
from dotenv import load_dotenv
from prompt_toolkit import print_formatted_text, HTML
import psutil

PROCWIFITCP = "wifi-tcp"

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
                    max_code_lines=100,
                    sdep_k=2,
                    sdep_p=30,
                    sdep_t=0
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
        # SDEP: targeted extinction
        self.sdep_k = sdep_k # how many generation ind are not improving
        self.sdep_p = sdep_p # probability of individual is extincted
        self.sdep_t = sdep_t # threshold regarding elite member
        self.sdep_last_best_fitness = 0
        self.sdep_current_stagnation = 0
        self.sdep_fresh_counter = 0
        self.last_best_individual_info = None
        self.last_best_individual = None
        self.ROOT_DIR = os.path.abspath(os.curdir)

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
                max_branch_depth=self.max_branch_depth,
                alpha_var_gen=self.alpha_var,
                value_bottom=self.value_bottom,
                value_upper=self.value_upper
            )
            indiv.id = i + loaded_pickle
            self.population.append(indiv)

    # @jit
    def calculate_fitness(self, generator):
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

        retry_counter = 1
        while retry_counter >= 0:
            try:
                print('configuring...')
                start = time.time()
                out = subprocess.check_output(configure_command, shell=True, timeout=20)
                end = time.time()
                print("configured in {:.3f} seconds".format(end - start))

                print('building...')
                start = time.time()
                try:
                    out = subprocess.check_output(build_command, shell=True, timeout=500)
                except Exception as e:
                    print("IMPOSSIBLE TO BUILD", e)
                    retry_counter -= 1
                    continue
                end = time.time()
                print("built in {:.3f} seconds".format(end - start))
                break
            except:
                print('error on configuring or building...')
                retry_counter -= 1
                continue
        
        if retry_counter == -1:
            # sys.exit("CRITICAL ERROR! CANNOT CONTINUE THE PROCESS, EXPORT A SNAPSHOT TO NOT LOSE THE PROGRESS")
            print("CRITICAL ERROR! CANNOT CONTINUE THE PROCESS, RETRY GENERATION")
            os.chdir(self.ROOT_DIR) # changing current directory
            subprocess.call('rm -Rf ./snapshots_pickles/{self.current_generation}_gen', shell=True)
            subprocess.call('rm -Rf ./snapshots/{self.current_generation}_gen', shell=True)
            self.hall_of_fame = self.hall_of_fame[:-1]
            self.current_generation -= 1
            os.chdir(self.ROOT_DIR)
            pickles = [f.path for f in os.scandir('./snapshots_pickles/{}_gen/'.format(self.current_generation))]
            self.init_population(generator, pickles)
            self.check_config_build()
            # subprocess.call('mv ./tmp/extract/snapshots/{}_gen.json init', shell=True)

        # print("calculating fitness...")
        #print("[{}] has fitness {}".format(0, self.population[0].max_fitness(0, self.fitness)))

        pool = Pool(pool_size)

        for idx, individual in enumerate(self.population):
            pool.apply_async(self.multiprocessing_fitness, (idx, individual))

        pool.close()
        pool.join()
        # subprocess.call(['killall', '-r', 'my_pattern'])

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
        if len(selected_individuals) >= k:
            while len(selected_individuals) < k:
                # picking random individual
                indiv = self.population[secrets.randbelow(self.pop_size)]
                # check if already picked
                if indiv in selected_individuals: continue
                # append individual
                selected_individuals.append(indiv)
        else:
            selected_individuals = self.population

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
            self.last_best_individual_info = {"id": self.population[0].id, "fitness": self.population[0].fitness, "gen": self.current_generation}
            self.last_best_individual = copy.deepcopy(self.population[0])
            return self.population[0] # return best individual
        elif self.current_gen > 1:
            return self.last_best_individual
        return None

    # @jit
    def crossover(self, best_individuals, there_is_elite, elite=None):
        # count how many offsprings to generate
        offsprings = self.DefaultConfig.TOURNAMENT['k'] - len(best_individuals)
        print("offsprings to generate are {}".format(offsprings))
        # reset population to best individuals
        self.population = []
        for b in best_individuals:
            self.population.append(copy.deepcopy(b))
        # create parent pool set
        parent_pool = set(best_individuals)
        if there_is_elite and elite is not None:
            parent_pool.add(copy.deepcopy(elite))
        
        place_for_elite = 1 if there_is_elite else 0
        counter_idx = len(self.population)+place_for_elite

        # generate new offsprings by
        while len(self.population) < self.pop_size-place_for_elite-self.sdep_fresh_counter: # -1 because elite individual is added afterwards
            # pick 2 random parents
            parents = []
            if len(parent_pool) > 0:
                for i in range(2):
                    parents.append(random.sample(parent_pool, 1)[0])

            variables = copy.deepcopy(self.variables)
            # self.population.append(generator.generate_individual_from_seed(variables=variables))
            indiv = generate_individual_from_seed(
                variables=variables,
                wildcard_codes=self.DefaultConfig.WILD_CARD_CODE,
                max_depth=self.max_depth,
                max_width=self.max_width,
                max_branch_depth=self.max_branch_depth,
                alpha_var_gen=self.alpha_var,
                value_bottom=self.value_bottom,
                value_upper=self.value_upper
            )
            indiv.id = counter_idx
            counter_idx += 1

            if len(parents) == 0:
                new_parent = generate_individual_from_seed(
                    variables=variables,
                    wildcard_codes=self.DefaultConfig.WILD_CARD_CODE,
                    max_depth=self.max_depth,
                    max_width=self.max_width,
                    max_branch_depth=self.max_branch_depth,
                    alpha_var_gen=self.alpha_var,
                    value_bottom=self.value_bottom,
                    value_upper=self.value_upper
                )
                new_parent.id = counter_idx
                counter_idx += 1
                parents.append(new_parent)
            
            print(RenderTree(parents[0].root))
            # convert nodes to sets
            parent_one_nodes = parents[0].root.descendants
            parent_two_nodes = indiv.root.descendants

            # parent_three_nodes = [n for n in PreOrderIter(parents[1].root.children[0])]
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
                first_child_branch = random.sample(child.root.descendants, 1)[0]
                # first_child_branch.children = [subtree_one]
                subtree_one.parent = first_child_branch

            if len(parent_two_nodes) > 1:
                subtree_two = copy.deepcopy(random.sample(parent_two_nodes, 1)[0])
                subtree_two.parent = None
                # perform crossover
                # second operation
                second_child_branch = random.sample(indiv.root.descendants, 1)[0]
                subtree_two.parent = second_child_branch

            # add child to population
            self.population.append(child)

    def rand_int(self, start, end):
        return random.randint(start, end-1)
    
    def extinct(self, y_prob=0):
        return True if self.rand_int(0, 1000) < y_prob*10 else False

    def mutate(self, y_prob=50.0):
        return True if self.rand_int(0, 1000) < y_prob*10 else False

    def mutate_switch_branches(self, y_prob=30):
        return True if self.rand_int(0, 1000) < y_prob*10 else False

    # @jit
    def mutation(self):
        for idx, individual in enumerate(self.population):
            if not isinstance(individual, Individual):
                print("ERROR added something different as individual")
                quit()
            counter = self.rand_int(1, self.max_mutations)
            while counter > 0:
                if self.mutate(y_prob=self.DefaultConfig.MUTATION['truncate_node']) and not individual.is_elite:
                    # truncate mutation
                    nodes = [node for node in PreOrderIter(individual.root)]
                    selected_node = nodes[secrets.randbelow(len(nodes))]
                    # selected_node.parent.children = []
                    selected_node.parent = None
                    counter -= 1
                if counter > 0 and \
                    self.mutate(y_prob=self.DefaultConfig.MUTATION['operator_flip']) and not individual.is_elite:
                    # operator flipping
                    if (len(individual.root.children) >= 1):

                        variables = copy.deepcopy(individual.variables)
                        random_node = random.sample(individual.root.children, 1)[0]
                        
                        print("----------------------------------------BEFORE----------------------------------------")
                        print(individual.render_code())
                        print("----------------------------------------MUTATE----------------------------------------")
                        
                        new_node = generate_operator_node(
                                        random_node.parent,
                                        variables=variables,
                                        wildcard_codes=self.DefaultConfig.WILD_CARD_CODE,
                                        max_depth=self.max_depth,
                                        max_width=self.max_width,
                                        max_branch_depth=self.max_branch_depth,
                                        alpha_var_gen=self.alpha_var,
                                        value_bottom=self.value_bottom,
                                        value_upper=self.value_upper
                                    )
                        for child in random_node.children:
                            child.parent = new_node
                        random_node.parent = None
                        del random_node
                        gc.collect()
                        # random_node.children = []
                        print(individual.render_code())
                        print("--------------------------------------------------------------------------------------")
                    counter -= 1
                # switch branches
                if counter > 0 and \
                    self.mutate_switch_branches(y_prob=self.DefaultConfig.MUTATION['switch_branches']):
                    for node in PreOrderIter(individual.root):
                        if isinstance(node, IfThenElse):
                            tmp = copy.deepcopy(node.exp_f)
                            node.exp_f = copy.deepcopy(node.exp_t)
                            node.exp_t = tmp
                            break
                    counter -= 1
                # switch compatible operators
                # for instance sum with multiplication
                if counter > 0 and \
                    self.mutate(y_prob=self.DefaultConfig.MUTATION['switch_exp']):
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
                    counter -= 1

    def sdep_f(self, x):
        '''
                    x^(1/2)
        f(x) = 10 --------------
                    1 + e^(-x)
        '''
        return 10 * ((x**(1/2))/(1+math.e**(-x)))

    def sdep(self):
        '''
        Stagnation-driven extinction protocol: Targeted Extinction
        https://www.mdpi.com/2076-3417/11/8/3461
        
        Notes:
            individuals are extincted with probability (sdep_p+sdep_f(sdep_current_stagnation-sdep_k)) 
            if their fitness is under a threshold calculated as elite_fitness*(1-sdep_t) if generations 
            are stagnant for sdep_k generations.
        '''
        print("[SDEP] running...")
        self.sdep_fresh_counter = 0
        extinction_probability = 0
        # if generation are stagnant more than the activation threshold
        if self.sdep_current_stagnation >= self.sdep_k:
            x = self.sdep_current_stagnation-self.sdep_k
            extinction_probability = self.sdep_p + self.sdep_f(x)

            extinct_individuals = []

            for ind in self.population:
                if ind.fitness <= self.sdep_last_best_fitness*(1-self.sdep_t) and \
                    self.extinct(y_prob=extinction_probability):
                    extinct_individuals.append(ind)
            
            self.sdep_fresh_counter = len(extinct_individuals)

            for ind in extinct_individuals:
                self.population.remove(ind)
        print("[SDEP] FRESH INDIVIDUALS: {} \t STAGNATION: {} \t EXTINCTION P: {:.2f}".format(
                                                self.sdep_fresh_counter, 
                                                self.sdep_current_stagnation,
                                                extinction_probability
                                            ))

    def check_config_build(self):
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

        retry_counter = 1
        while retry_counter >= 0:
            try:
                print('configuring...')
                start = time.time()
                out = subprocess.check_output(configure_command, shell=True, timeout=20)
                end = time.time()
                print("configured in {:.3f} seconds".format(end - start))

                print('building...')
                start = time.time()
                try:
                    out = subprocess.check_output(build_command, shell=True, timeout=500)
                except Exception as e:
                    print("IMPOSSIBLE TO BUILD", e)
                    retry_counter -= 1
                    continue
                end = time.time()
                print("built in {:.3f} seconds".format(end - start))
                break
            except:
                print('error on configuring or building...')
                retry_counter -= 1
                continue
        
        if retry_counter == -1:
            print("CRITICAL ERROR! CANNOT CONTINUE THE PROCESS, RETRY GENERATION")
            os.chdir(self.ROOT_DIR) # changing current directory
            subprocess.call('rm -Rf ./snapshots_pickles/{self.current_generation}_gen', shell=True)
            subprocess.call('rm -Rf ./snapshots/{self.current_generation}_gen', shell=True)
            self.hall_of_fame = self.hall_of_fame[:-1]
            print("Retry generating population...")
            return False
        return True

    def run(self, generator, pickles=[]):
        # writing that simulation is running
        path_termination_flag = os.path.join(sys.path[0], 'termination_flag')
        with open(path_termination_flag, 'w') as termination_flag:
            termination_flag.write('RUNNING')
        
        self.ROOT_DIR = os.path.abspath(os.curdir)
        # init population giving a generator
        self.init_population(generator, pickles)

        for i in range(self.generations):
            # take snapshot of generated individuals
            self.take_snapshot()

            #self.mutation()
            #break

            self.calculate_fitness(generator)

            elite_individual = copy.deepcopy(self.add_hall_of_fame(add_to_elite=True))

            if elite_individual is not None:
                if self.sdep_last_best_fitness != elite_individual.fitness:
                    self.sdep_current_stagnation = 0
                else:
                    self.sdep_current_stagnation += 1    
                self.sdep_last_best_fitness = elite_individual.fitness
            else:
                self.sdep_current_stagnation += 1

            # apply SDEP
            self.sdep()

            # write out the hall of fame
            path_folder_hall = os.path.join(sys.path[0], "snapshots")
            path_file_hall = "{}/hall_of_fame.json".format(path_folder_hall)
            with open(path_file_hall, 'w') as out_hall:
                json.dump(self.hall_of_fame, out_hall)

            print("[GENERATION {}/{}] with population:".format(self.current_generation, self.pop_size))

            for idx, ind in enumerate(self.population):
                ind.id = idx
                print("id:{}, fitness:{:.2f}, variables: {}".format(ind.id,ind.fitness, ind.variables.variables_name()))

            selected = self.tournament_selection(
                k=self.DefaultConfig.TOURNAMENT["k"],
                s=self.DefaultConfig.TOURNAMENT["s"])

            # print("[GENERATION {}/{}] HALL OF FAME: {}".format(self.current_generation, self.pop_size, [str(ind) for ind in self.hall_of_fame]))
            print_formatted_text(HTML(
                "<aaa fg=\"white\" bg=\"red\"><b>[GENERATION {}/{}] HALL OF FAME: {}</b></aaa>".format(self.current_generation, self.generations, [str(ind) for ind in self.hall_of_fame])
            ))


            print("{} SELECTED INDIVIDUALS".format(len(selected)))

            for idx, ind in enumerate(selected):
                print("id:{}, fitness:{:.2f}".format(ind.id, ind.fitness))

            # self.population = []
            there_is_elite = elite_individual is not None
            if len(selected) >= 2:
                self.crossover(selected, there_is_elite=there_is_elite, elite=elite_individual)
                # self.fix_not_valid_crossover()

            self.mutation()

            # fixing individual
            for ind in self.population:
                variables = copy.deepcopy(self.variables)
                # updating variables
                ind.update_variable_registry(variables)

            counter_idx = len(self.population)
            # inject fresh individuals from extinction
            for i in range(self.sdep_fresh_counter):
                variables = copy.deepcopy(self.variables)
                indiv = generate_individual_from_seed(
                    variables=variables,
                    wildcard_codes=self.DefaultConfig.WILD_CARD_CODE,
                    max_depth=self.max_depth,
                    max_width=self.max_width,
                    max_branch_depth=self.max_branch_depth,
                    alpha_var_gen=self.alpha_var,
                    value_bottom=self.value_bottom,
                    value_upper=self.value_upper
                )
                indiv.id = counter_idx
                counter_idx += 1

                # add indiv to population
                self.population.append(copy.deepcopy(indiv))
                print("FRESH INDIVIDUAL CODE: {}".format(indiv.render_code()))


            if len(selected) == 0:
                print("GOT NOT AVAILABLE INDIVIDUALS")
                self.population = []
                self.init_population(generator, pickles)

            # cleaning ID
            for idx, individual in enumerate(self.population):
                individual.id = idx

            if elite_individual is not None:
                # print("[ELITE INDIVIDUAL] id:{}, fitness:{}".format(elite_individual.id, elite_individual.fitness))
                print_formatted_text(HTML(
                    "<aaa fg=\"black\" bg=\"yellow\"><b>[ELITE INDIVIDUAL] id:{}, fitness:{}</b></aaa>".format(elite_individual.id, elite_individual.fitness)
                ))
                elite_individual.id = len(self.population)
                self.population.append(elite_individual)

            self.current_generation += 1
            self.current_gen = []
            gc.collect()

            for proc in psutil.process_iter():
                # check whether the process name matches
                if proc.name() == PROCWIFITCP:
                    proc.kill()

        print("FINAL POPULATION")
        print([ind.fitness for ind in self.population])
        print("HALL OF FAME:")
        print([str(ind) for ind in self.hall_of_fame])

        # write out the hall of fame
        path_folder_hall = os.path.join(sys.path[0], "snapshots")
        path_file_hall = "{}/hall_of_fame.json".format(path_folder_hall)
        with open(path_file_hall, 'w') as out_hall:
            json.dump(self.hall_of_fame, out_hall)
        # writing that simulation has stopped
        with open(path_termination_flag, 'w') as termination_flag:
            termination_flag.write('STOP')

    def kill(self):
        sys.exit()


