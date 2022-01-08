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
from utils.fitness import tcp_variant_fitness_write_switch
from pathlib import Path
import time
import base64

load_dotenv()

BASE_NS3_PATH = os.getenv('BASE_NS3_PATH')
ROOT_DIR = os.path.abspath(os.curdir)

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
        os.chdir(ROOT_DIR)
        # empty switch case
        tcp_variant_fitness_write_switch([''])
        subprocess.call('rm -rf *.out', shell=True)
        subprocess.call('rm -rf ./snapshots/current_gen.json', shell=True)
        subprocess.call('rm -rf ./snapshots/hall_of_fame.json', shell=True)
        subprocess.call('rm -rf ./init', shell=True)
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
        subprocess.call('rm -rf ./snapshots/*', shell=True)        
        subprocess.call('rm -rf ./snapshots_pickles/*', shell=True)
        subprocess.call('rm termination_flag', shell=True)
        return {'msg': 'completed!'}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}

@app.route("/ns3reset")
def ns3reset():
    try:
        os.chdir(ROOT_DIR)
        dir_to_change = '{}/'.format(BASE_NS3_PATH)
        os.chdir(dir_to_change)
        subprocess.call(['./waf', 'clean'])
        return {'msg': 'completed!'}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}

@app.route("/ns3baseline")
def ns3baseline():
    try:
        os.chdir(ROOT_DIR)
        baseline = 0
        fname = 'baseline'
        
        if os.path.isfile(fname):
            with open(fname, 'r') as b_file:
                baseline = float(b_file.read())
            return {'msg': 'Baseline Calculated!', 'baseline': baseline}

        clean()
        dir_to_change = '{}/'.format(BASE_NS3_PATH)
        os.chdir(dir_to_change)
        out = subprocess.check_output('./run.sh', shell=True, timeout=120, stderr=subprocess.DEVNULL)
        values = out.decode("utf-8").replace("\n", " ").split()
        values = [float(value) for value in values]
        
        if len(values) > 0:
            baseline = sum(values) / len(values)
        
        os.chdir(ROOT_DIR)
        with open(fname, 'w') as b_file:
            b_file.write("{}".format(baseline))
        
        return {'msg': 'Baseline Calculated!', 'baseline': baseline}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}

@app.route("/autofix")
def autofix():
    try:
        os.chdir(ROOT_DIR)
        clean()
        dir_to_change = '{}/'.format(BASE_NS3_PATH)
        os.chdir(dir_to_change)
        subprocess.call(['./waf', 'clean'])
        subprocess.call(['./waf', 'build'])
        return {'msg': 'Autofixing Completed!'}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}

@app.route("/snapshot")
def snapshot():
    try:
        os.chdir(ROOT_DIR)
        config_data = request.args.get('config')
        with open('./config.json', 'w') as b_file:
            b_file.write("{}".format(config_data))
        os.chdir(ROOT_DIR)
        Path("tmp").mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        fname = 'tmp/{}_snapshot.zip'.format(ts)
        # out = '{}.out'.format(worker.get_pid())
        command = 'zip -r {} snapshots snapshots_pickles config.json *.out'.format(fname)
        subprocess.call(command, shell=True)
        subprocess.call('rm -rf config.json', shell=True)
        with open(fname, 'rb') as fin:
            bytes = fin.read()
            encoded = base64.b64encode(bytes).decode("utf-8")
        
        return {'msg': 'Zipped Snapshot in Tmp!', 'zip': encoded, 'filename': '{}_snapshot.zip'.format(ts)}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}

@app.route("/snapshot/restore", methods=['POST'])
def snapshot_restore():
    try:
        os.chdir(ROOT_DIR)
        Path("tmp").mkdir(parents=True, exist_ok=True)
        subprocess.call('rm -rf ./tmp/*', shell=True)
        file = request.files['snapshot']
        file.save('tmp/{}'.format(file.filename))
        subprocess.call('rm -rf ./tmp/extract', shell=True)
        subprocess.call(['unzip', 'tmp/{}'.format(file.filename), '-d', 'tmp/extract'])

        config = None
        if os.path.isfile('tmp/extract/config.json'):
            with open('tmp/extract/config.json', 'rb') as config_json:
                config = json.load(config_json)

        hall_of_fame = None
        if os.path.isfile('tmp/extract/snapshots/hall_of_fame.json'):
            with open('tmp/extract/snapshots/hall_of_fame.json', 'rb') as hf_json:
                hall_of_fame = json.load(hf_json)


        subfolders = [ int(f.path.split('/')[-1:][0].replace('_gen', '')) for f in os.scandir('tmp/extract/snapshots_pickles') if f.is_dir() ]
        subfolders.sort(reverse=True)

        tot_pop = sum([len(files) for r, d, files in os.walk('tmp/extract/snapshots_pickles/{}_gen'.format(subfolders[0]))])
        os.chdir(ROOT_DIR)
        Path("init").mkdir(parents=True, exist_ok=True)
        subprocess.call('rm -rf ./init/*', shell=True)
        subprocess.call('mv ./tmp/extract/snapshots_pickles/{}_gen init'.format(subfolders[0]), shell=True)
        subprocess.call('mv ./tmp/extract/snapshots/hall_of_fame.json init', shell=True)
        subprocess.call('rm -rf ./tmp', shell=True)
        path_final = os.path.join(ROOT_DIR, 'init', '{}_gen'.format(subfolders[0]))
        files = os.listdir(path_final)
        print(files)
        with open('init/info', 'w', encoding='utf-8') as b_file:
            json.dump({'pop_size': tot_pop, 
                        'hall_of_fame': hall_of_fame, 
                        'pickles': ['{}/{}'.format(path_final, f) for f in files]}, b_file)

        # Path("tmp").mkdir(parents=True, exist_ok=True)
        # ts = int(time.time())
        # fname = 'tmp/{}_snapshot.zip'.format(ts)
        # subprocess.call(['zip', '-r', fname, 'snapshots', 'snapshots_pickles'])
        # with open(fname, 'rb') as fin:
        #     bytes = fin.read()
        #     encoded = base64.b64encode(bytes).decode("utf-8")
        
        return {'msg': 'Successfully setted initial population from Snapshot!', 'config': config, 'hall_of_fame': hall_of_fame}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}  


@app.route('/check_status', methods=["GET"])
def check_status():
    try:
        simulation_running = False
        status = None
        if os.path.exists("./termination_flag"):
            with open('./termination_flag', 'r') as f:
                status = f.readline()
                if status == "STOP":
                    simulation_running = False
                elif status == "RUNNING":
                    simulation_running = True
        
        config = {}
        if os.path.exists("./config.json"):
            with open('./config.json', 'r') as b_file:
                config = json.load(b_file)

        hall_of_fame = None
        if os.path.isfile('./snapshots/hall_of_fame.json'):
            with open('./snapshots/hall_of_fame.json', 'rb') as hf_json:
                hall_of_fame = json.load(hf_json)

        return {
            'msg': 'Current Status information.',
            "running": simulation_running,
            "config": config,
            'hall_of_fame': hall_of_fame,
            "status": status
        }

    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}            


@app.route("/run", methods=["POST"])
def run():
    try:
        os.chdir(ROOT_DIR)
        print(request)
        sim_data = request.get_json()
        config_data = request.args.get('config')
        with open('./config.json', 'w') as b_file:
            b_file.write("{}".format(config_data))
        os.chdir(ROOT_DIR)
        print(sim_data)
        pickles = []
        if os.path.isdir('./init') and os.path.isfile('./init/info'):
            with open('init/info', 'r') as f:
                pickle_data = json.load(f)
                if int(pickle_data['pop_size']) <= int(sim_data['pop']):
                    pickles = pickle_data['pickles']
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
            sim_data['max_mutations'],
            sim_data['value_bottom_limit'],
            sim_data['value_top_limit'],
            sim_data['max_code_lines'],
            sim_data['max_depth'],
            sim_data['max_width'],
            sim_data['alpha_vars'],
            sim_data['max_branch_depth'],
            sim_data['payload_size'],
            sim_data['simulation_time'],
            sim_data['mtu_bottom_limit'],
            sim_data['mtu_upper_limit'],
            sim_data['mtu_step'],
            sim_data['wildcards'],
            sim_data['variables'],
            pickles
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
        os.chdir(ROOT_DIR)
        f = open('./snapshots/current_gen.json')
        individuals = json.load(f)
        f.close()
        return {'msg': 'completed!', 'individuals': individuals}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}

@app.route("/hall")
def hall():
    try:
        os.chdir(ROOT_DIR)
        f = open('./snapshots/hall_of_fame.json')
        individuals = json.load(f)
        f.close()
        return {'msg': 'completed!', 'individuals': individuals}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}

@app.route("/log")
def log():
    try:
        os.chdir(ROOT_DIR)
        buffer = ""
        if worker.is_alive():
            pid = worker.get_pid()
            # print("pid is {}".format(pid))
            buffer = subprocess.check_output(["cat", "{}.out".format(str(pid))])
            buffer = buffer.decode("utf-8") #.replace("\n", "<br>")

            # buffer = worker.get_log()
        return {'msg': 'completed!', 'buffer': buffer}
    except Exception as e:
        return {'mgs': 'Exception {} occured.'.format(e)}


# if __name__ == "__main__":
app.run(debug=False, threaded=True)

