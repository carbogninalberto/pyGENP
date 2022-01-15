import os
import re
import sys

print(sys.argv)

ROOT_FOLDER = sys.argv[1] if len(sys.argv) > 1 else './results/compactor_tests'
FILE = "{}.cc".format(sys.argv[2] if len(sys.argv) > 2 else '29')
FILE_COMPACTED = "{}_compacted.cc".format(sys.argv[2] if len(sys.argv) > 2 else '29')


REGEX_DECLARE_INT = r'(?<=int\s)(.*)(?=\s=\s.*;)'
REGEX_DECLARE_FLOAT = r'(?<=float\s)(.*)(?=\s=\s.*;)'
REGEX_USAGE_ASSIGNMENT = '.*(?<=\s=\s)({})(?=.*;)'
REGEX_USAGE_ASSIGNMENT_LINE = '.*\s=\s.*({})(?=.*;)' #'[.*\s=\s.*]*({})(?=.*;)'
REGEX_USAGE_IF_THEN_ELSE = 'if\s\(.*({})'
REGEX_IS_IF = '^if\s\(.*.*\).*$'
REGEX_EXPRESSION = '\((\(?\d+.?\d*\)*(\*|\+|\-|\/)?)+'
REGEX_MATH_EXP = '[[\(]?[-]?\d[\.\d]*[\)]?[\+\-\/\*]?'
REGEX_MATCH_THE_EXPRESSION = '[\(]*[-]?\d[\.\d]*[\)]?[\(]?[-]?[a-zA-Z\d\-\+\*\/\(\)\.\_\>]*[\)]?[\+\-\/\*]?'

# old regex just for ref.
#'[\(]*[-]?\d[\.\d]*[\)]?[\+\-\/\*]*[\(]?[-]?[a-zA-Z\d\-\+\*\/\(\)\.\_\>]*[\)]*[\+\-\/\*]?'
#'[[\(]?[-]?\d[\.\d]*[\)]?[[\(]?[-]?[a-zA-Z\d\-\+\*\/\(\)\.\_\>]*[\)]?[\+\-\/\*]?'

lines = []
output_lines = []

with open(os.path.join(ROOT_FOLDER,FILE), 'r') as file:
    lines = file.readlines();

    #### REMOVING EMPTY LINES
    output_lines = []
    for line in lines:
        if line.strip() != "":
            output_lines.append(line)


    #### GATHERING VARIABLES NAME
    output_lines_tmp = output_lines.copy() #output_lines.copy()
    output_lines = []
    variables = []
    for line in output_lines_tmp:
        declaring_int = re.search(REGEX_DECLARE_INT, line)
        # print(declaring_int)
        if declaring_int:
            name = declaring_int.group()
            if name != 'i':
                variables.append(name)
            # variables.append()
        declaring_float = re.search(REGEX_DECLARE_FLOAT, line)
        # print(declaring_float)
        if declaring_float:
            name = declaring_float.group()
            if name != 'i':
                variables.append(name)
    print("variables: {}".format(variables))

    #### REMOVE IF UNUSED
    variables_to_use = []
    for var in variables:
        for line in output_lines_tmp:
            usage_assignment = re.search(REGEX_USAGE_ASSIGNMENT_LINE.format(var), line)
            # print("usage_assignment -> {}".format(usage_assignment))
            if usage_assignment and var not in variables_to_use:
                variables_to_use.append(var)
                continue
            
            usage_ifthenelse = re.search(REGEX_USAGE_IF_THEN_ELSE.format(var), line)
            if usage_ifthenelse and var not in variables_to_use:
                variables_to_use.append(var)
                continue
    print("variables to use: {}".format(variables_to_use))

    for var in variables:
        if var not in variables_to_use:
            for line in output_lines_tmp:

                var_contained = re.search(var, line)
                if var_contained:
                    continue

                output_lines.append(line)
            output_lines_tmp = output_lines.copy()
            output_lines = []
    
    output_lines = output_lines_tmp.copy()
    output_lines_tmp = []

    # ### CLEAN EMPTY IF THEN ELSE
    prev = None
    for idx, line in enumerate(output_lines):
        # print("prev -> {}".format(prev))
        if re.match(REGEX_IS_IF, line.strip()) and idx < len(output_lines)-1 and output_lines[idx+1].strip() == '} else {' \
            and line.strip().count('{') == 1 and line.strip().count('}') != 1:
            # output_lines_tmp.append(prev)
            if prev is not None:
                output_lines_tmp.append(prev)
            # print("----muted by if")
            # print("found if -> {}".format(line))
            prev = None
            continue
        elif prev is not None and prev.strip() == '} else {' and line.strip() == '}':
            # print("found else -> {}".format(line))
            # print("----muted by else")
            prev = None
            continue
        elif prev is not None:
            output_lines_tmp.append(prev)
        
        if line.strip() != '':
            prev = line
        else:
            prev = None
    
    # print("prev -> {}".format(prev))
    output_lines_tmp.append(prev)
    output_lines = output_lines_tmp.copy()
    output_lines_tmp = []
    
    ### SIMPLIFY EXPRESSION
    for idx, line in enumerate(output_lines):
        line_tmp = line
        # matches = re.search(REGEX_EXPRESSION, line_tmp.strip())
        matches = re.search(REGEX_MATCH_THE_EXPRESSION, line_tmp.strip())        
        if matches:
            match = matches.group()
            # parse if contains variables
            try:
                if match[-1:] in ['*', '/', '-', '+']:
                    match = match[:-1]
                    if match[:1] == "(" and match.count('(') > match.count(')'):
                        match = match[1:]
                if match[-1:] == ')' and match.count('(') < match.count(')'):
                    match = match[:-1]
                    
                line_tmp = line_tmp.replace(str(match), str(round(eval(match), 3)))
            except Exception as e:
                print("CANNOT SIMPLIFY EXPRESSIONS WITH VARIABLES")
            output_lines_tmp.append(line_tmp)
        else:
            output_lines_tmp.append(line)

    output_lines = []

    #### COMPRESSING EQUAL CODE LINES INTO A FOR LOOP
    loop_lines = []
    prev = None
    c = 0
    for line in output_lines_tmp.copy():
        line = line.strip()
        if prev == line:
            loop_lines.append(line)
        elif line != prev and len(loop_lines) > 0:
            output_lines.append("""\nfor (int i = 0; i < {0}; i++) {{ \n\t{1}\n}}\n\n""".format(len(loop_lines)+1, loop_lines[0]))
            output_lines.append("{}\n".format(line))
            loop_lines = []
            prev = None
            continue
        elif prev is not None and len(loop_lines) == 0:
            output_lines.append("{}\n".format(prev))
        if line != '':
            prev = line
        else:
            prev = None
    if prev is not None and len(loop_lines) == 0:
        output_lines.append("{}\n".format(prev))
    else:
        output_lines.append("""\nfor (int i = 0; i < {0}; i++) {{ \n\t{1}\n}}\n\n""".format(len(loop_lines)+1, loop_lines[0]))


with open(os.path.join(ROOT_FOLDER,FILE_COMPACTED), 'w+') as file:
    file.writelines(output_lines)