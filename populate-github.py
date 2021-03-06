#!/usr/bin/env python

import sys
import json
import re
import random
import os.path
import time
from config import Config
from github import Github
from github import GithubException

class CannotAddUserToRepo(Exception):
    pass

def usage(pname):
        print("Usage: {} <github username> <github password> <json config file>".format(pname))

def config(args):
    if len(args) != 4:
        pname = os.path.basename(args[0])
        usage(pname)
        sys.exit(1)
    return (args[1], args[2], args[3])

def main():
    (user,password,conf_file) = config(sys.argv)

    # Read in json config (generated with generate_config.py)
    # with open(conf_file, 'r') as f:
    #     conf_json = json.load(f)

    # # seed RNG based on assignment name
    # seed = Config.java_string_hashcode(conf.assignment_name)
    # random.seed(seed)

    conf = Config([sys.argv[0], conf_file])
    conf.pretty_print()

    # connect to github
    g = Github(user, password)
    guser = g.get_user()
    org = g.get_organization("williams-cs")

    for repo_name,group in conf.repo2group.items():
        repo = None
        try:
            # check to see if repository already exists
            repo = org.get_repo(repo_name)
        except GithubException:
            # if not, create repository
            # auto_init=False so no README.md, license.txt, .gitignore --- use push-starter.py after running this script
            print("creating repository {}".format(repo_name))
            repo = org.create_repo(repo_name,
                               description=(" and ".join(group) + "'s " + conf.course + " repository for " + conf.assignment_name + "."),
                               private=True,
                               auto_init=False
            )
            
        # add write privs for each student login
        for student in group:
            print("getting user for {}".format(student))
            suser = g.get_user(student)

            # at this point, the repository is guaranteed to exist, but
            # sometimes Github will return a 404 for recently-created repositories
            retries = 3
            success = False
            while retries > 0:
                try:           
                    # add student as write-enabled collaborator
                    print("adding {} as collaborator to {} repository.".format(student, repo_name))
                    repo.add_to_collaborators(suser)
                    retries = 0
                    success = True
                except GithubException:
                    retries -= 1
                    print("Could not find repository " + repo_name + ".  Sleeping...")
                    time.sleep(5)    # wait 5 seconds
            if not success:
                raise CannotAddUserToRepo

if __name__ == "__main__":
    main()
