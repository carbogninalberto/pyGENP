import json
import statistics
from ast import parse

ALGORITHMS = [
    'TcpNewReno', 
    'TcpBic'#,
    # 'TcpHybla',
    # 'TcpHighSpeed',
    # 'TcpHtcp',
    # 'TcpVegas',
    # 'TcpScalable',
    # 'TcpVeno',
    # 'TcpYeah',
    # 'TcpIllinois',
    # 'TcpWestwood',
    # 'TcpWestwoodPlus',
    # 'TcpLedbat'
]
PAYLOAD_SIZES = [250, 1500, 3000, 7500, 15000]

PARSED_LINES = []

OUTPUT_JSON = {}

for algorithm in ALGORITHMS:
    OUTPUT_JSON[algorithm] = {}
    for payload_size in PAYLOAD_SIZES:
        OUTPUT_JSON[algorithm][payload_size] = {"values": []}

with open('all_2.out', 'r') as baselines:
    lines = baselines.readlines()
    for line in lines:
        parsed_line = list(filter(lambda x: x != "Mbit/s", line.split()))
        if parsed_line[0] in ALGORITHMS:
            PARSED_LINES.append(parsed_line)
    # print(PARSED_LINES)

for parsed_line in PARSED_LINES:
    for i, p_size in enumerate(PAYLOAD_SIZES):
        OUTPUT_JSON[parsed_line[0]][p_size]['values'].append(float(parsed_line[i+1]))

# print(OUTPUT_JSON)

for algorithm in ALGORITHMS:
    for payload_size in PAYLOAD_SIZES:
        sample = []
        sum = 0
        for value in OUTPUT_JSON[algorithm][payload_size]['values']:
            sum += value
            sample.append(value)
        mean = sum/10

        std = statistics.stdev(sample)
        OUTPUT_JSON[algorithm][payload_size]["mean"] = format(round(mean, 2), '.2f')
        OUTPUT_JSON[algorithm][payload_size]["std"] = format(round(std, 2), '.2f')
        OUTPUT_JSON[algorithm][payload_size]["top"] = format(round(mean+std, 2), '.2f')
        OUTPUT_JSON[algorithm][payload_size]["bottom"] = format(round(mean-std, 2), '.2f')

with open('baselines2.json', 'w') as baselines:
    json.dump(OUTPUT_JSON, baselines, indent=2)


TABLE_LINES = []

for algorithm in ALGORITHMS:
    current_line = "{}".format(algorithm)
    for payload_size in PAYLOAD_SIZES:
        current_line += " & ${} \pm {}$".format(OUTPUT_JSON[algorithm][payload_size]["mean"], OUTPUT_JSON[algorithm][payload_size]["std"])
    current_line += " \\\\\n"
    TABLE_LINES.append(current_line)

with open("latex_table2", "w") as l_table:
    l_table.writelines(TABLE_LINES)

# TcpNewReno & 35.030 & 52.013 & 53.715 & 54.250 & 55.650 \\
# TcpBic & 35.514 & 52.337 & 54.320 & 54.787 & 55.575 \\
# TcpHybla & 35.559 & 52.090 & 53.335 & 54.262 & 55.650 \\
# TcpHighSpeed & 34.803 & 51.970 & 53.360 & 55.862 & 55.375 \\
# TcpHtcp & 35.045 & 52.407 & 53.490 & 54.362 & 54.325 \\
# TcpVegas & 28.630 & 54.683 & \textbf{55.395} & \textbf{57.162} & 54.800 \\
# TcpScalable & 35.417 & 52.552 & 53.130 & 54.425 & 54.500 \\
# TcpVeno & 35.083 & 52.528 & 53.555 & 55.450 & 55.200 \\
# TcpYeah & 35.109 & 52.173 & 53.795 & 54.862 & 54.325 \\
# TcpIllinois & 35.053 & 52.612 & 53.920 & 54.837 & 55.575 \\
# TcpWestwood & 35.060 & 52.135 & 53.705 & 54.325 & 55.350 \\
# TcpWestwoodPlus & \textbf{35.829} & 51.937 & 54.275 & 55.075 & 55.750 \\
# TcpLedbat & 35.061 & 52.758 & 53.985 & 55.062 & 55.250 \\
