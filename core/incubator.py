from .types import DefaultConfig

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
                ):
        
        self.DefaultConfig = DefaultConfig
        self.pop_size = pop_size
        self.generations = generations
        self.population = []
        self.fitness = fitness
        self.variables = variables
    
    def init_population(self, generator):
        for i in range(self.pop_size):
            self.population.append(generator.generate_individual_from_seed(variables=self.variables))

    def calculate_fitness(self):
        for idx, individual in enumerate(self.population):
            # print(">>>>>>>>>>>FITNESS>>>>>>>>>>>")
            print("[{}] has fitness {}".format(idx, individual.max_fitness(self.fitness)))

    def tournament_selection(self):
        return None
