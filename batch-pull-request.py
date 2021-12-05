#!/usr/bin/env python

import sys
from typing import Sequence, Tuple

from github import Github

from Infrastructor import Infrastructor


def usage(pname: str) -> None:
    print(f"Usage: {pname} <github username> <github password> <config.json>")


def parse_args(args: Sequence[str]) -> Tuple[str, str, str]:
    if len(args) != 4:
        usage(args[0])
        sys.exit(1)
    else:
        return args[1], args[2], args[3]


def main() -> None:
    # get config
    user, passwd, cfile = parse_args(sys.argv)
    infra = Infrastructor([sys.argv[0], cfile])
    conf = infra.config

    # init Github SDK
    g = Github(user, passwd)
    # guser = g.get_user()
    org = g.get_organization("williams-cs")

    # TODO: verify that local repo is on the correct branch
    basepath = conf.submission_path
    for repo in conf.repositories():
        # get submissions dir path for repo
        rdir = infra.pull_path(conf, basepath, repo, False,
                               conf.anonymize_sub_path)
        if not infra.branch_exists(conf, rdir):
            print(f"No feedback branch for {rdir}")
            continue
        # issue pull request for given repo
        print(f"issuing pull request for {rdir}")
        infra.issue_pull_request(conf, rdir, org)


if __name__ == "__main__":
    main()
