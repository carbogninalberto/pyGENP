import os
import sys

def count_tabs(text):
    counter = 0
    for i in range(len(text)):
        if i+1 < len(text)-1:
            print(text[i], text[i+1])
            if text[i] == "\\" and text[i+1] == "t":
                counter += 1
    return counter

def parser(file='prova.cc', substitute_lines=["std::cout << i << std::endl;"]):
    open_file = open(os.path.join(sys.path[0], file), 'r')
    print(os.path.join(sys.path[0], file))
    lines = open_file.readlines()
    parsed_file_lines = []
    tag_o, tag_c = False, False # open tag
    for line in lines:
        print("|{}|".format(line.strip() == "//REPLACE"))
        if line.strip() == "//REPLACE" and not tag_c:
            tabs = count_tabs(line)
            tabs_append = ""
            for i in range(tabs):
                tabs_append += "\t"
            if tag_o:
                for substitute in substitute_lines:
                    parsed_file_lines.append("{}{}\n".format(tabs_append, substitute))
                tag_c = True
            tag_o = True
        else:
            parsed_file_lines.append(line)
    return parsed_file_lines

def output_parsed_file(file='prova_parsed.cc', lines=[]):
    with open(os.path.join(sys.path[0], file), 'w') as f:
        f.writelines(lines)
    f.close()

# out = parser()
# print(out)
# output_parsed_file(lines=out)