#!/usr/bin/env python

import json
import random
from typing import List, Dict

import argparse

from utils import group2repo, java_string_hashcode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="prints the contents of a config file to standard out.")
    parser.add_argument("sfile", type=str,
                        help="student name file")
    parser.add_argument("base_config", type=str,
                        help="base config template")

    args = parser.parse_args()
    with open(args.base_config, 'r') as f:
        conf = json.load(f)

    # seed RNG based on assignment name
    seed = java_string_hashcode(conf["assignment_name"])
    random.seed(seed)

    # read student names from input file
    groups: List[List[str]] = []
    f = open(args.sfile)
    for line in f:
        group = line.rstrip().split(",")
        groups.append(group)
    f.close()

    # "randomly" shuffle group list
    random.shuffle(groups)

    # pair students with repositories
    repo_map: Dict[str, str] = {}
    for group in groups:
        # synthesize repo name
        repo = group2repo(
            conf["course"], conf["assignment_name"], group)
        for student in group:
            # add pairing to json
            repo_map[student] = repo

    # print config
    conf["repository_map"] = repo_map

    print(json.dumps(conf, indent=4, sort_keys=True))


if __name__ == "__main__":
    main()
