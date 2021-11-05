import os
import subprocess
from .parser import parser_wrapper
from dotenv import load_dotenv
from numba import jit

load_dotenv()

BASE_NS3_PATH = os.getenv('BASE_NS3_PATH')

# @jit
def tcp_variant_fitness(idx):
    payload = 1500
    dir_to_change = '{}/'.format(BASE_NS3_PATH)
    os.chdir(dir_to_change)
    # os.chdir('{}/ns-3.32/'.format(BASE_NS3_PATH))
    # os.chdir('/mnt/c/Users/carbo/Desktop/Unitn/tesi/ns-allinone-3.32.2/ns-allinone-3.32/ns-3.32/')
    #out = os.popen('./waf --run "scratch/wifi-tcp --tcpVariant=TcpHighSpeed --payloadSize={} --simulationTime=2"| tail -10 | grep -P \'(?<=: \t)(.*)(?= Mbit\/s)\' -o'.format(payload))
    #print(out, type(out))
    #os.system('CXXFLAGS="-Wall -g -O0" ./waf configure')
    #out = subprocess.check_output('CXXFLAGS="-Wno-error" ./waf --run "scratch/wifi-tcp --payloadSize={} --simulationTime=2" | tail -10 | grep -P \'(?<=: \\t)(.*)(?= Mbit\/s)\' -o'.format(payload), shell=True)
    out = b''
    retry = True
    counter = 0
    while retry:
        try:
            out = subprocess.check_output('range={} ./run.sh'.format(idx), shell=True, timeout=60)
            retry = False
        except Exception as e:
            print("EXCEPTION", e)
            if counter > -1:
                return -1
            else:
                counter += 1
    values = out.decode("utf-8").replace("\n", " ").split()
    values = [float(value) for value in values]
    if len(values) > 0:
        #print(values)
        #average = sum(values) / len(values)
        # print("out", out, "values", values)
        return sum(values) / len(values)
    else:
        return 0

def tcp_variant_fitness_wrapped(idx, lines=[]):
    #parser_wrapper(file='/mnt/c/Users/carbo/Desktop/Unitn/tesi/ns-allinone-3.32.2/ns-allinone-3.32/ns-3.32/src/internet/model/tcp-congestion-ops.cc', lines=lines)
    if len(lines) < 5 or len(lines) > 100:
        return -1
    else:
        return tcp_variant_fitness(idx)


def tcp_variant_fitness_write_switch(lines=[]):
    parser_wrapper(file='{}/src/internet/model/tcp-congestion-ops.cc'.format(BASE_NS3_PATH), lines=lines)
