#!/usr/bin/env python

import argparse
import os
import subprocess
import sys

from Infrastructor import Infrastructor


def dump_file(fname: str) -> None:
    with open(fname, 'r') as fin:
        for line in fin:
            print(line, end='')


def main() -> None:
    # get config
    parser = argparse.ArgumentParser(
        description='Run a command (e.g., autograding script) in each TA '
                    'folder. Optionally dump the output to a file in the '
                    'repository.')
    parser.add_argument('config', type=str,
                        help='config file for the lab')
    parser.add_argument('command', type=str,
                        help='bash command to run in each "TA" repo. Passed '
                             'to Popen')
    parser.add_argument('output_file', type=str,
                        help='File (in each repo) where output is stored.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='enable verbose output')

    args = parser.parse_args()

    infra = Infrastructor([sys.argv[0], args.config])
    conf = infra.config

    # basepath = conf.ta_path
    for repo in conf.repositories:
        ta_dir = conf.TA_target(conf.ta_path, conf.assignment_name, repo)
        print(f"{repo}: {ta_dir}")
        with subprocess.Popen(args=args.command.split(),
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              universal_newlines=True,
                              cwd=ta_dir) as proc:
            output = proc.stdout.read()
            with open(os.path.join(ta_dir, args.output_file), 'a') as fout:
                print(output, file=fout)


if __name__ == "__main__":
    main()
