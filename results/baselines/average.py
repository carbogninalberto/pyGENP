

def average(lines):
    sum = 0
    for line in lines:
        sum += float(line)
    return sum/float(len(lines))

print("BASELINE for 30 seconds run")

with open('./tcpBic_30_baseline', 'r') as bic:
    lines = bic.readlines()
    print("TCP BIC AVERAGE: {:.5f}".format(average(lines)))

with open('./tcpNewReno_30_baseline', 'r') as new_reno:
    lines = new_reno.readlines()
    print("TCP NEW RENO AVERAGE: {:.5f}".format(average(lines)))

with open('./tcpNewReno_30_baseline2', 'r') as new_reno:
    lines = new_reno.readlines()
    print("TCP NEW RENO AVERAGE 2: {:.5f}".format(average(lines)))