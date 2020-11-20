#!/usr/bin/env python

import sys
import json
import re
import random
import os.path
from config import Config
from github import Github

def usage(pname):
        print("Usage: {} <student name file> <base config template>".format(pname))
        print("\t>> prints the contents of a config file to standard out.")

def config(args):
    if len(args) != 3:
        pname = os.path.basename(args[0])
        usage(pname)
        sys.exit(1)
    return (args[1], args[2])

def main():
    (sfile,base_config) = config(sys.argv)
    with open(base_config, 'r') as f:
        conf = json.load(f)

    # seed RNG based on assignment name
    seed = Config.java_string_hashcode(conf["assignment_name"])
    random.seed(seed)

    # read student names from input file
    groups = []
    f = open(sfile)
    for line in f:
        group = line.rstrip().split(",")
        groups.append(group)
    f.close()

    # "randomly" shuffle group list
    random.shuffle(groups)

    # pair students with repositories
    repo_map = {}
    for group in groups:
        # synthesize repo name
        repo = Config.group2repo(conf["course"], conf["assignment_name"], group)
        for student in group:
            # add pairing to json
            repo_map[student] = repo

    # print config
    conf["repository_map"] = repo_map

    print(json.dumps(conf, indent=4, sort_keys=True))

if __name__ == "__main__":
    main()
