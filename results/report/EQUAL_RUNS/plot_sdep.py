import json
import os
import matplotlib.pyplot as plt
import statistics
import math
import numpy as np

def sdep_f(x):
    '''
                x^(1/2)
    f(x) = 10 --------------
                1 + e^(-x)
    '''
    return 10 * ((x**(1/2))/(1+math.e**(-x)))



baselineY = [sdep_f(i) for i in range(30)]
baselineX = [i for i in range(30)]


plt.plot(baselineX, baselineY)
plt.xlabel("Generation (after threshold activation)")
plt.ylabel("Probability (%)")

plt.xticks(np.arange(min(baselineX), max(baselineX)+1, 2))

# Show the plot
# plt.show()
figure = plt.gcf()
figure.set_size_inches(7, 4)
plt.savefig('plot_sdep_function.svg', dpi=72)