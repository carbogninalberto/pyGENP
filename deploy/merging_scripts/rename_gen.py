'''
You may want to continue the run from a snapshot and merge it later on.
This script helps you doing it.
'''
import os
import json
import subprocess

src = input("src: ")
from_gen = input("from: ")
dirs = os.scandir(src)
dirs = [ int(f.path.split('/')[-1:][0].replace('_gen', '')) for f in os.scandir(src) if f.is_dir() ]
dirs.sort()
start = int(from_gen)

for dir in dirs:
    print("dir", dir)
    subprocess.call(['mv', os.path.join(src, '{}_gen'.format(dir)), os.path.join(src, '{}_gen'.format(start))])
    start += 1

hf = []
with open(os.path.join(src, 'hall_of_fame.json'), 'rb') as hf_json:
    hall_of_fame = json.load(hf_json)
    start = int(from_gen)
    for i in hall_of_fame:
        i['gen'] = start
        hf.append(i)
        start +=1
        print(i)

with open(os.path.join(src, 'hall_of_fame.json'), 'w+') as hf_json:
    json.dump(hf, hf_json)

