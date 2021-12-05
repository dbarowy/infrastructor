#!/usr/bin/env python

import sys
from typing import Tuple, Sequence

from github import Github

from Infrastructor import Infrastructor


def usage(pname: str) -> None:
    print(f"Usage: {pname} <github username> <github password> "
          f"<repository name> <config.json>")


def parse_args(args: Sequence[str]) -> Tuple[str, str, str, str]:
    if len(args) != 5:
        usage(args[0])
        sys.exit(1)
    else:
        return args[1], args[2], args[3], args[4]


def main() -> None:
    # get config
    user, passwd, repo, cfile = parse_args(sys.argv)
    infra = Infrastructor([sys.argv[0], cfile])
    conf = infra.config

    # init Github SDK
    g = Github(user, passwd)
    # guser = g.get_user()
    org = g.get_organization("williams-cs")

    # TODO: verify that local repo is on the correct branch

    # issue pull request for given repo
    infra.issue_pull_request(conf, repo, org)


if __name__ == "__main__":
    main()
