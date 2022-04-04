import os
import sys
import subprocess
import json
from random import randint
from dotenv import load_dotenv

load_dotenv()

BASE_NS3_PATH = os.getenv('BASE_NS3_PATH')

SECONDS = 5
# ALGORITHMS = [
#     'TcpNewReno', 
#     'TcpBic',
#     'TcpHybla',
#     'TcpHighSpeed',
#     'TcpHtcp',
#     'TcpVegas',
#     'TcpScalable',
#     'TcpVeno',
#     'TcpYeah',
#     'TcpIllinois',
#     'TcpWestwood',
#     'TcpWestwoodPlus',
#     'TcpLedbat'
# ]

ALGORITHMS = [
    'TcpNewReno', 
    'TcpBic'
]
PAYLOAD_SIZES = [250, 1500, 3000, 7500, 15000]

OUTPUT_JSON = {}

for algorithm in ALGORITHMS:
    OUTPUT_JSON[algorithm] = {}
    for payload_size in PAYLOAD_SIZES:
        OUTPUT_JSON[algorithm][payload_size] = []

if len(sys.argv) > 1:
    ALGORITHMS = [sys.argv[1]]

if len(sys.argv) > 2:
    SECONDS = int(sys.argv[2])

# with open('baselines2.json', 'r') as baselines:
#     print(baselines.readLines())

# if len(ALGORITHMS) == 1:
#     print(ALGORITHMS[0])
#     os.chdir(BASE_NS3_PATH)
#     averages = []
#     out = subprocess.check_output('./random_seed_run.sh {} {} {} {}'.format(ALGORITHMS[0], SECONDS, randint(1, 1000000), 250), 
#                                             shell=True, timeout=1200, stderr=subprocess.DEVNULL)
#     values = out.decode("utf-8").replace("\n", " ").split()
#     values = [float(value) for value in values]
#     if len(values) > 0:
#         averages.append(sum(values) / len(values))

#     print(averages)


print("CONFIGURATION")
print("Simulation Duration: {}s".format(SECONDS))
print('----------------------------------------------------'*3)
print('{0:<20} {1:<23} {2:<23} {3:<23} {4:<23} {5:<23}'
        .format('algorithm', 
                'throughput ({} B)'.format(PAYLOAD_SIZES[0]),
                'throughput ({} B)'.format(PAYLOAD_SIZES[1]),
                'throughput ({} B)'.format(PAYLOAD_SIZES[2]),
                'throughput ({} B)'.format(PAYLOAD_SIZES[3]),
                'throughput ({} B)'.format(PAYLOAD_SIZES[4])))
print('----------------------------------------------------'*3)

os.chdir(BASE_NS3_PATH)
for trial in range(10):
    for i, algorithm in enumerate(ALGORITHMS):
        averages = []
        for j, payload_size in enumerate(PAYLOAD_SIZES):
            SEED = randint(1, 1000000)
            print('[{}/{}] algorithm calculating {}/{} for payload size {} bytes...\r'.format(
                i+1, len(ALGORITHMS),
                j+1, len(PAYLOAD_SIZES),
                payload_size), end='', flush=True)
            try:
                out = subprocess.check_output('./random_seed_run.sh {} {} {} {}'.format(algorithm, SECONDS, SEED, payload_size), 
                                                shell=True, timeout=1200, stderr=subprocess.DEVNULL)
                values = out.decode("utf-8").replace("\n", " ").split()
                values = [float(value) for value in values]
                if len(values) > 0:
                    averages.append(sum(values) / len(values))

            except Exception as e:
                print("EXCEPTION", e)

        print('{0:<20} {1:<5.3f} Mbit/s           {2:<5.3f} Mbit/s           {3:<5.3f} Mbit/s           {4:<5.3f} Mbit/s           {5:<5.3f} Mbit/s'
        .format(algorithm, averages[0], averages[1], averages[2], averages[3], averages[4]))

        for j, payload_size in enumerate(PAYLOAD_SIZES):
            OUTPUT_JSON[algorithm][payload_size].append(averages[j])

    print('----------------------------------------------------'*3)

with open('baselines2.json', 'w+') as baselines:
    json.dump(OUTPUT_JSON, baselines, indent=2)