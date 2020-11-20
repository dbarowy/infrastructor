#!/usr/bin/env python

import sys
from config import Config
from github import Github

def usage(pname):
        print("Usage: {} <github username> <github password> <config.json>".format(pname))

def parse_args(args):
    if len(args) != 4:
        usage(args[0])
        sys.exit(1)
    else:
        return (args[1], args[2], args[3])

def main():
    # get config
    user, passwd, cfile = parse_args(sys.argv)
    conf = Config([sys.argv[0], cfile])

    # init Github SDK
    g = Github(user, passwd)
    guser = g.get_user()
    org = g.get_organization("williams-cs")

    # TODO: verify that local repo is on the correct branch
    basepath=conf.submission_path
    for repo in conf.repositories():
            # get submissions dir path for repo
            rdir = conf.pull_path(basepath, repo, False, conf.anonymize_sub_path)
            if not conf.branch_exists(rdir):
                    print("No feedback branch for {}".format(rdir))
                    continue
            # issue pull request for given repo
            print("issuing pull request for {}".format(rdir))
            conf.issue_pull_request(rdir, org)

if __name__ == "__main__":
    main()
