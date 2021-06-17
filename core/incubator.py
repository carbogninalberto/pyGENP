from types import DefaultConfig


class Incubator:

    def __init__(
                    self,
                    config=DefaultConfig,
                    pop_size=50,
                    generations=100,
                    alfa_var_gen=12.0,
                    const_termination_range=[-20, 20]
                ):
        
        self.DefaultConfig = DefaultConfig
        self.pop_size = 50
        self.generations = 100