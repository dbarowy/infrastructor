#!/usr/bin/env python

import sys
from config import Config
from github import Github

def usage(pname):
        print("Usage: {} <github username> <github password> <repository name> <config.json>".format(pname))

def parse_args(args):
    if len(args) != 5:
        usage(args[0])
        sys.exit(1)
    else:
        return (args[1], args[2], args[3], args[4])

def main():
    # get config
    user, passwd, repo, cfile = parse_args(sys.argv)
    conf = Config([sys.argv[0], cfile])

    # init Github SDK
    g = Github(user, passwd)
    guser = g.get_user()
    org = g.get_organization("williams-cs")

    # TODO: verify that local repo is on the correct branch

    # issue pull request for given repo
    conf.issue_pull_request(repo, org)

if __name__ == "__main__":
    main()
