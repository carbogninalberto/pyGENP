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
