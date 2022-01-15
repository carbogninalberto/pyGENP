import os
import sys
import json

ROOT_FOLDER = sys.argv[1] if len(sys.argv) > 1 else './results/compactor_tests'
FILE_COMPACTED = "{}_compacted.cc".format(sys.argv[2] if len(sys.argv) > 2 else '29')
OUTPUT_FOLDER = './docs/code'
JSON_FILE = sys.argv[3] if len(sys.argv) > 3 else 'test.json'
RUN_NUMBER = sys.argv[4] if len(sys.argv) > 4 else 'run_empty'

code = ""
with open(os.path.join(ROOT_FOLDER,FILE_COMPACTED), 'r') as file:
    code = file.read()

loaded_code_json = {}
code_file_path = os.path.join(OUTPUT_FOLDER, JSON_FILE)
# when there is the file we need to load it
if os.path.exists(code_file_path):
    print("EXISTS")
    with open(code_file_path, 'r') as code_json:
        loaded_code_json = json.load(code_json)

loaded_code_json[RUN_NUMBER] = code

with open(code_file_path, 'w+') as code_json:
    json.dump(loaded_code_json, code_json, indent=2)