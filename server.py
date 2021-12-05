from flask import Flask, send_from_directory, request
import random
import subprocess
import os
import json
from core import individual
from dotenv import load_dotenv
# import threading
from multiprocessing import Process
from sim import SimThread

load_dotenv()

BASE_NS3_PATH = os.getenv('BASE_NS3_PATH')

app = Flask(__name__)

pids_not_to_kill = (subprocess.check_output(["pidof", "python"])).decode("utf-8").replace("\n", " ").split()

worker = Process() #threading.Thread()

# Path for our main Svelte page
@app.route("/")
def base():
    return send_from_directory('webapp/public', 'index.html')

# Path for all the static files (compiled JS/CSS, etc.)
@app.route("/<path:path>")
def home(path):
    return send_from_directory('webapp/public', path)


@app.route("/rand")
def hello():
    return str(random.randint(0, 100))


@app.route("/clean")
def clean():
    try:
        subprocess.call('rm *.out', shell=True)
        subprocess.call('rm snapshots/current_gen.json', shell=True)
        subprocess.call('rm snapshots/hall_of_fame.json', shell=True)
        # print(worker.is_alive())
        # print(worker.native_id)
        # if worker.is_alive():
        #     # worker.terminate()
        #     worker.join()
        #     worker.kill()
        #     # subprocess.call(['kill', '-9', str(worker.native_id)])
        #     # worker.terminate()
        #     # worker.join()
        #     worker.kill()
        # print(worker.get_pid())
        # worker.join()
        if worker.is_alive():
            print("{} is alive!".format(worker.get_pid()))
            worker.kill()
        # worker.do_run = False
        pids = subprocess.check_output(["pidof", "python"])
        pids = pids.decode("utf-8").replace("\n", " ").split()
        print(pids_not_to_kill)
        for pid in pids:
            print(pid)
            if str(pid) not in pids_not_to_kill:
                subprocess.call(['kill', '-9', str(pid)])
        subprocess.call(['pkill' ,'-f', 'wifi-tcp'])
        subprocess.call(['rm' ,'-rf', 'snapshots/*'])        
        subprocess.call(['rm' ,'-rf', 'snapshots_pickles/*'])
        return {'msg': 'completed!'}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}

@app.route("/ns3reset")
def ns3reset():
    try:
        dir_to_change = '{}/'.format(BASE_NS3_PATH)
        os.chdir(dir_to_change)
        subprocess.call(['./waf', 'clean'])
        return {'msg': 'completed!'}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}

@app.route("/run", methods=["POST"])
def run():
    try:
        print(request)
        sim_data = request.get_json()
        print(sim_data)
        global worker
        worker = SimThread(
            sim_data['pop'],
            sim_data['gen'],
            sim_data['k'],
            sim_data['s'],
            sim_data['operator_flip'],
            sim_data['switch_branches'],
            sim_data['switch_exp'],
            sim_data['truncate_node'],
        )
        # sim_thread.setDaemon(True)
        worker.start()        
        
        # worker = sim_thread
        return {'msg': 'Run started!'}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}


@app.route("/gen/current")
def gen_current():
    try:
        # individuals = []
        # if worker is not None:
        #     individuals = worker.get_current_gen()
        f = open('snapshots/current_gen.json')
        individuals = json.load(f)
        f.close()
        return {'msg': 'completed!', 'individuals': individuals}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}

@app.route("/hall")
def hall():
    try:
        # individuals = []
        # if worker is not None:
        #     individuals = worker.get_current_gen()
        f = open('snapshots/hall_of_fame.json')
        individuals = json.load(f)
        f.close()
        return {'msg': 'completed!', 'individuals': individuals}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}

@app.route("/log")
def log():
    try:
        buffer = ""
        if worker.is_alive():
            pid = worker.get_pid()
            print("pid is {}".format(pid))
            buffer = subprocess.check_output(["cat", "{}.out".format(str(pid))])
            buffer = buffer.decode("utf-8") #.replace("\n", "<br>")

            # buffer = worker.get_log()
        return {'msg': 'completed!', 'buffer': buffer}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}


# if __name__ == "__main__":
app.run(debug=True)

