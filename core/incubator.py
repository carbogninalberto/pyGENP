from .types import DefaultConfig

class Incubator:

    def __init__(
                    self,
                    config=DefaultConfig,
                    pop_size=2,
                    generations=20,
                    alfa_var_gen=12.0,
                    const_termination_range=[-20, 20],
                    fitness=None,
                ):
        
        self.DefaultConfig = DefaultConfig
        self.pop_size = 50
        self.generations = 100
        self.population = []
        self.fitness = fitness
    
    def init_population(self, generator):
        for i in range(self.pop_size):
            self.population.append(generator.generate_individual_from_seed())

    def calculate_fitness(self):
        for idx, individual in enumerate(self.population):
            print(">>>>>>>>>>>FITNESS>>>>>>>>>>>")
            print("[{}] has fitness {}".format(idx, individual.max_fitness(self.fitness)))
