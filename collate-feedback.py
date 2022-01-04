#!/usr/bin/env python

import os

import argparse

from Infrastructor import Infrastructor
from config import Config
from utils import self_check


def dump_file(fname: str) -> None:
    with open(fname, 'r') as fin:
        for line in fin:
            print(line, end='')


def main() -> None:
    # get config
    parser = argparse.ArgumentParser(
        description='collect the contents of all README.md files into one '
                    'place, labeled by GitHub ID in order to update '
                    'gradebooks')
    parser.add_argument('config', type=str,
                        help='config file for the lab')
    parser.add_argument('feedback_file', type=str,
                        help='file in repo where feedback is left (often '
                             'README.md)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='enable verbose output')

    args = parser.parse_args()

    self_check()
    conf = Config(args.config, args.verbose)

    for student in sorted(conf.list_of_users):
        repo = conf.lookupRepo(student)

        # get submissions dir path for repo
        rdir = conf.pull_path(conf.submission_path, repo, False,
                              conf.anonymize_sub_path)

        # all graded labs should have a feedback branch
        # if not infra.branch_exists(rdir):
        #     print("\n\n")
        #     print("# ERROR for {}".format(student))
        #     print("# No feedback branch in {}".format(rdir))
        #     print("\n\n")
        #     continue

        # dump username and README.md contents to stdout
        print(f"# BEGIN {student} FEEDBACK")
        print(f"__({rdir})__")
        dump_file(os.path.join(rdir, args.feedback_file))
        print(f"## END {student} FEEDBACK")
        print("\n\n")


if __name__ == "__main__":
    main()
