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
    parser.add_argument("repo", type=str,
                        help="github repository name")
    parser.add_argument('config', type=str,
                        help='config file for the lab')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='enable verbose output')

    args = parser.parse_args()
    self_check()
    # get config
    conf = Config(args.config, args.verbose)

    # init Github SDK
    g = Github(args.user, args.password)
    # guser = g.get_user()
    org = g.get_organization("williams-cs")

    # TODO: verify that local repo is on the correct branch

    # issue pull request for given repo
    Infrastructor.issue_pull_request(conf, args.repo, org)


if __name__ == "__main__":
    main()
