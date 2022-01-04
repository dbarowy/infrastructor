#!/usr/bin/env python
import time

import argparse
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

    self_check()
    conf = Config(args.config, args.verbose)
    conf.pretty_print()

    # connect to github
    g = Github(args.user, args.password)
    org = g.get_organization("williams-cs")

    for repo_name, group in conf.repo2group.items():
        # repo = None
        try:
            # check to see if repository already exists
            repo = org.get_repo(repo_name)
        except GithubException:
            # if not, create repository
            # auto_init=False so no README.md, license.txt, .gitignore ---
            # use push-starter.py after running this script
            print(f"creating repository {repo_name}")
            repo = org.create_repo(repo_name,
                                   description=(" and ".join(group) + "'s " +
                                                conf.course + "repository for "
                                                + conf.assignment_name + "."),
                                   private=True,
                                   auto_init=False
                                   )

        # add write privs for each student login
        for student in group:
            print(f"getting user for {student}")
            suser = g.get_user(student)

            # at this point, the repository is guaranteed to exist,
            # but sometimes Github will return a 404 for recently-created
            # repositories
            retries = 3
            success = False
            while retries > 0:
                try:
                    # add student as write-enabled collaborator
                    print(f"adding {student} as collaborator to {repo_name} "
                          f"repository.")
                    repo.add_to_collaborators(suser)
                    retries = 0
                    success = True
                except GithubException:
                    retries -= 1
                    print(f"Could not find repository {repo_name}. "
                          f"Sleeping...")
                    time.sleep(5)  # wait 5 seconds
            if not success:
                raise CannotAddUserToRepo


if __name__ == "__main__":
    main()
