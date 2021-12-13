#!/usr/bin/env python

import argparse
from github import Github

from Infrastructor import Infrastructor
from config import Config
from utils import self_check


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("user", type=str,
                        help="github username")
    parser.add_argument("password", type=str,
                        help="github password")
    parser.add_argument('config', type=str,
                        help='config file for the lab')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='enable verbose output')

    args = parser.parse_args()
    # get config
    self_check()
    conf = Config(args.config, args.verbose)

    # init Github SDK
    g = Github(args.user, args.password)
    # guser = g.get_user()
    org = g.get_organization("williams-cs")

    # TODO: verify that local repo is on the correct branch
    basepath = conf.submission_path
    for repo in conf.repositories:
        # get submissions dir path for repo
        rdir = conf.pull_path(basepath, repo, False, conf.anonymize_sub_path)
        if not Infrastructor.branch_exists(conf, rdir):
            print(f"No feedback branch for {rdir}")
            continue
        # issue pull request for given repo
        print(f"issuing pull request for {rdir}")
        Infrastructor.issue_pull_request(conf, rdir, org)


if __name__ == "__main__":
    main()
