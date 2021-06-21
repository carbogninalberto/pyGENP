import os
import subprocess
from .parser import parser_wrapper

def tcp_variant_fitness():
    payload = 1500
    os.chdir('/home/alberto/ns-allinone-3.32/ns-3.32/')
    #out = os.popen('./waf --run "scratch/wifi-tcp --tcpVariant=TcpHighSpeed --payloadSize={} --simulationTime=2"| tail -10 | grep -P \'(?<=: \t)(.*)(?= Mbit\/s)\' -o'.format(payload))
    #print(out, type(out))
    #os.system('CXXFLAGS="-Wall -g -O0" ./waf configure')
    #out = subprocess.check_output('CXXFLAGS="-Wno-error" ./waf --run "scratch/wifi-tcp --payloadSize={} --simulationTime=2" | tail -10 | grep -P \'(?<=: \\t)(.*)(?= Mbit\/s)\' -o'.format(payload), shell=True)
    out = subprocess.check_output('./run.sh', shell=True)
    values = out.decode("utf-8").replace("\n", " ").split()
    values = [float(value) for value in values]
    #print(values)
    #average = sum(values) / len(values)
    print("values")
    return sum(values) / len(values)

def tcp_variant_fitness_wrapped(lines=[]):
    parser_wrapper(file='/home/alberto/ns-allinone-3.32/ns-3.32/src/internet/model/tcp-congestion-ops.cc', lines=lines)
    return tcp_variant_fitness()
