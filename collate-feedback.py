#!/usr/bin/env python

import argparse
import os
import sys

from Infrastructor import Infrastructor


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

    infra = Infrastructor([sys.argv[0], args.config])
    conf = infra.config

    for student in sorted(infra.list_of_users(conf)):
        repo = infra.lookupRepo(conf, student)

        # get submissions dir path for repo
        rdir = infra.pull_path(conf, conf.submission_path, repo, False,
                               conf.anonymize_sub_path)

        # all graded labs should have a feedback branch
        # if not conf.branch_exists(rdir):
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
