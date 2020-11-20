#!/usr/bin/env python

import argparse
import sys
import os
from config import Config
from github import Github


def dump_file(fname) :
    with open(fname, 'r') as fin :
        for line in fin:
            print(line, end='')

def main():
    # get config
    parser = argparse.ArgumentParser(description='collect the contents of all README.md files into one place, labeled by GitHub ID in order to update gradebooks')
    parser.add_argument('config', type=str,
                        help='config file for the lab')
    parser.add_argument('feedback_file', type=str,
                        help='file in repo where feedback is left (often README.md)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='enable verbose output')

    args = parser.parse_args()

    conf = Config([sys.argv[0], args.config])

    for student in sorted(conf.list_of_users()):
        repo = conf.lookupRepo(student)

        # get submissions dir path for repo
        rdir = conf.pull_path(conf.submission_path, repo, False,
                              conf.anonymize_sub_path)

        # all graded labs should have a feedback branch
        # if not conf.branch_exists(rdir):
        #     print("\n\n")
        #     print("# ERROR for {}".format(student))
        #     print("# No feedback branch in {}".format(rdir))
        #     print("\n\n")
        #     continue

        # dump username and README.md contents to stdout
        print("# BEGIN {} FEEDBACK".format(student))
        print("__({})__".format(rdir))
        dump_file(os.path.join(rdir, args.feedback_file))
        print("## END {} FEEDBACK".format(student))
        print("\n\n")

if __name__ == "__main__":
    main()
