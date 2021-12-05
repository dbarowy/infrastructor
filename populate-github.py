#!/usr/bin/env python

import os.path
import sys
import time
from typing import Sequence, Tuple

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

    infra = Infrastructor([sys.argv[0], conf_file])
    conf = infra.config
    conf.pretty_print()

    # connect to github
    g = Github(user, password)
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
