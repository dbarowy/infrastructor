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
            ans = input("delete repository {}? (y/n) ".format(repo_name))
            if ans == "y":
                repo.delete()
        except GithubException:
            print("GitHubException. We could not delete repository {}".format(repo_name))
            

if __name__ == "__main__":
    main()
