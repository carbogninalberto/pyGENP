# PYGENP Genetic Programming library
A (very) essential Genetic Programming library in Python. 

```
The code in this repository is experimental and unstable.
```

## Quick Ref
In order to evolve a set of individuals you need to define custom **operators** or use the one provided by default.
Moreover, you can specify a set of **variable** to use, by **injecting** a initialization value or specify that value is provided by outter **scope**.

The concept of **scope** is important, as long as the root node rappresents the main scope of the evolved program, which could of course contain inner scopes. 

### Registry
There are 2 main registers: **Variables** and **Operators** used in mutation and in random tree generation for the initial population:

- **Variables Registry**: this registry contains all the initialize variables, it enables dynamic variables adding, and variable value mutation in the lifecycle;
- **Operators Registry**: this registry contains all the pre-define operators, it is useful to introduce novelty in the program and complex data manipulation. 

### Parent Selection, Crossover and Mutation
By default **tournament selection** is performed to select the best individuals, that will go to next generation as is and will be also used as genetic parents pool to perform **crossover** and **mutation** for the next generation.  

The following hyperparameters could be customized:

- tournament_size: the number of individual to select for a tournament
- best_individuals: the number of individual to take as-is for the next generation
- replace_individuals: the number of individual to replace (a value between best_individuals < replace_individuals < MAX_POP_SIZE)

#### Crossover
In this phase random part of a individual tree are cutted off and replaced with random ones of a selected parent.

#### Mutation
Different mutations are performed:
- Flib Bit: random number of boolean values are inverted
- Constant Add: a random value is added to constants
- Operator Flip: a operator is flipped with another


### Fitness Calculation
Is possible to provide a custom fitness function and also specify if maximize or minimize it.
