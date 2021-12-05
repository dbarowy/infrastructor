#!/usr/bin/env python

import os.path
import sys
from typing import Tuple, Sequence

from github import Github
from github import GithubException

from Infrastructor import Infrastructor


class CannotAddUserToRepo(Exception):
    pass


def usage(pname: str) -> None:
    print(f"Usage: {pname} <github username> <github password> "
          f"<json config file>")


def config(args: Sequence[str]) -> Tuple[str, str, str]:
    if len(args) != 4:
        pname = os.path.basename(args[0])
        usage(pname)
        sys.exit(1)
    return args[1], args[2], args[3]


def main() -> None:
    (user, password, conf_file) = config(sys.argv)

    # Read in json config (generated with generate_config.py)
    # with open(conf_file, 'r') as f:
    #     conf_json = json.load(f)

    # # seed RNG based on assignment name
    # seed = Config.java_string_hashcode(conf.assignment_name)
    # random.seed(seed)

    infra = Infrastructor([sys.argv[0], conf_file])
    conf = infra.config
    infra.pretty_print(conf)

    # connect to github
    g = Github(user, password)
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
