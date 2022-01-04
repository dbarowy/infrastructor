#!/usr/bin/env python
import argparse
import os.path
import sys
from typing import Tuple, Sequence

from github import Github
from github import GithubException

from Infrastructor import Infrastructor
from config import Config
from utils import self_check


class CannotAddUserToRepo(Exception):
    pass


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

    # Read in json config (generated with generate_config.py)
    # with open(conf_file, 'r') as f:
    #     conf_json = json.load(f)

    # # seed RNG based on assignment name
    # seed = Config.java_string_hashcode(conf.assignment_name)
    # random.seed(seed)

    self_check()
    conf = Config(args.config, args.verbose)
    conf.pretty_print()

    # connect to github
    g = Github(args.user, args.password)
    # guser = g.get_user()
    org = g.get_organization("williams-cs")

    for repo_name, group in conf.repo2group.items():
        # repo = None
        try:
            # check to see if repository already exists
            repo = org.get_repo(repo_name)
            ans = input(f"delete repository {repo_name}? (y/n) ")
            if ans == "y":
                repo.delete()
        except GithubException:
            print(f"GitHubException. "
                  f"We could not delete repository {repo_name}")


if __name__ == "__main__":
    main()
