import os
import sys

def count_tabs(text):
    counter = 0
    for i in range(len(text)):
        if i+1 < len(text)-1:
            #print(text[i], text[i+1])
            if text[i] == "\\" and text[i+1] == "t":
                counter += 1
    return counter

def parser(file='default_file.cc', substitute_lines=[""], tag="//REPLACE", output_tag=True, indent=""):
    """this function reads a c++ source code and update the lines in between a specified tag.

    Keyword Arguments:
        file {str} -- source code (default: {'default_file.cc'})
        substitute_lines {list} -- a list of lines to replace (default: {[""]})
        tag {str} -- the tag to looking for (default: {"//REPLACE"})
        output_tag {bool} -- specify if the tag should also be written in the output (default: {True})
        indent {str} -- apply a tab or spaces to all the input lines (default: {""})

    Returns:
        {list} -- return the file in the shape of a list of string, where each element is a line
    """    
    # open the file
    open_file = open(os.path.join(sys.path[0], file), 'r')
    # put lines in a list
    lines = open_file.readlines()
    # specify the list to be populated and returned
    parsed_file_lines = []
    # open and close tag condition variables
    tag_o, tag_c = False, False # open tag
    # read each line
    for line in lines:
        # if there is a tag and it's not the closing tag
        if line.strip() == tag and not tag_c:
            # count the number of tabs to replicate
            tabs = count_tabs(line)
            tabs_append = "" + indent
            for i in range(tabs):
                tabs_append += "\t"
            
            # if the tag is open
            if tag_o:
                for substitute in substitute_lines:
                    parsed_file_lines.append("{}{}\n".format(tabs_append, substitute))
                tag_c = True
            
            parsed_file_lines.append(tag + "\n")
            tag_o = True
        elif not tag_o or tag_c:
            # just append line as it is
            parsed_file_lines.append(line)
    return parsed_file_lines

def output_parsed_file(file='prova_parsed.cc', lines=[]):
    with open(os.path.join(sys.path[0], file), 'w') as f:
        f.writelines(lines)
    f.close()


def parser_wrapper(file='', lines=[]):
    out = parser(file=file, substitute_lines=lines)
    output_parsed_file(file=file, lines=out)


# out = parser()
# print(out)
# output_parsed_file(lines=out)