import json
import os
import matplotlib.pyplot as plt
import statistics
import numpy as np

baselineY = [52.337 for i in range(50)]
baselineX = [i+1 for i in range(50)]

ALGO = "json50bic"
# ALGO = "json50"

BASELINES = {}
# ALGORITHM = "TcpNewReno" # "TcpBic"
ALGORITHM = "TcpBic"
PAYLOAD_SIZE = "1500"

with open('baselines.json', 'r') as baselines:
    BASELINES = json.load(baselines)

runs = []
files = os.listdir(ALGO)
n_files = len(files)

for json_file in files:
    run = []
    with open(os.path.join(ALGO, json_file), 'r') as f:
        j = json.load(f)
        for fit in j:
            run.append(fit['fitness'])
    runs.append(run)




plt.plot(baselineX,
    [BASELINES[ALGORITHM][PAYLOAD_SIZE]["mean"] for i in range(50)], '--',
    color='red'
)

plt.fill_between(baselineX, 
                    [BASELINES[ALGORITHM][PAYLOAD_SIZE]["top"] for i in range(50)], 
                    [BASELINES[ALGORITHM][PAYLOAD_SIZE]["bottom"] for i in range(50)],
                    facecolor="orange", # The fill color
                    color='red',       # The outline color
                    alpha=0.1)          # Transparency of the fill

average = []
y1 = []
y2 = []

for x in range(50):
    sample = []
    sum = 0
    for run in runs:
        sum += run[x]
        sample.append(run[x])
    mean = sum/n_files;
    average.append(mean)

    std = statistics.stdev(sample)
    y1.append((sum/n_files)+std)
    y2.append((sum/n_files)-std)


plt.plot(baselineX, average)
plt.xlabel("Generation")
plt.ylabel("Throughput (Mbit/s)")

# Shade the area between y1 and y2
plt.fill_between(baselineX, y1, y2,
                 facecolor="orange", # The fill color
                 color='blue',       # The outline color
                 alpha=0.1)          # Transparency of the fill
plt.xticks(np.arange(min(baselineX)-1, max(baselineX)+1, 5))

plt.text(44.6, 54.92, 'fitness')
# plt.text(43.3, 54.82, 'fitness')

# plt.text(38.3, 52.10, 'TCP NewReno', color='red')
plt.text(44, 52.2, 'TCP Bic', color='red')
# Show the plot
# plt.show()
figure = plt.gcf()
figure.set_size_inches(7, 4)
plt.savefig(ALGO+'_results/plot.svg', dpi=30)