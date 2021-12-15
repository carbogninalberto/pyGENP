import json
import os
import matplotlib.pyplot as plt
import statistics

baselineY = [52.639411764706 for i in range(20)]
baselineX = [i+1 for i in range(20)]


runs = []
files = os.listdir('json')
n_files = len(files)

for json_file in files:
    run = []
    with open(os.path.join('json', json_file), 'r') as f:
        j = json.load(f)
        for fit in j:
            run.append(fit['fitness'])
    runs.append(run)

plt.plot(baselineX,baselineY, '--',
    color='red'
)

average = []
y1 = []
y2 = []

for x in range(20):
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
plt.xticks(baselineX)

plt.text(17.5, 54.9, 'fitness')

plt.text(17.5, 52.75, 'baseline', color='red')
# Show the plot
# plt.show()
plt.savefig('plot.png', dpi=92)