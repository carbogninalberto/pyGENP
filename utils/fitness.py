import os
import subprocess
from .parser import parser_wrapper

def tcp_variant_fitness():
    payload = 1500
    os.chdir('/mnt/c/Users/carbo/Desktop/Unitn/tesi/ns-allinone-3.32.2/ns-allinone-3.32/ns-3.32/')
    #out = os.popen('./waf --run "scratch/wifi-tcp --tcpVariant=TcpHighSpeed --payloadSize={} --simulationTime=2"| tail -10 | grep -P \'(?<=: \t)(.*)(?= Mbit\/s)\' -o'.format(payload))
    #print(out, type(out))
    #os.system('CXXFLAGS="-Wall -g -O0" ./waf configure')
    #out = subprocess.check_output('CXXFLAGS="-Wno-error" ./waf --run "scratch/wifi-tcp --payloadSize={} --simulationTime=2" | tail -10 | grep -P \'(?<=: \\t)(.*)(?= Mbit\/s)\' -o'.format(payload), shell=True)
    out = b''
    try:
        out = subprocess.check_output('./run.sh', shell=True)
    except:
        print("exception")
    values = out.decode("utf-8").replace("\n", " ").split()
    values = [float(value) for value in values]
    if len(values) > 0:
        #print(values)
        #average = sum(values) / len(values)
        # print("out", out, "values", values)
        return sum(values) / len(values)
    else:
        return 0

def tcp_variant_fitness_wrapped(lines=[]):
    parser_wrapper(file='/mnt/c/Users/carbo/Desktop/Unitn/tesi/ns-allinone-3.32.2/ns-allinone-3.32/ns-3.32/src/internet/model/tcp-congestion-ops.cc', lines=lines)
    return tcp_variant_fitness()
