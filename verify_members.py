#!/usr/bin/env python

import sys
from config import Config
from github import Github

def usage(pname):
        print("Usage: {} <github username> <github password> <org name> <student_file>".format(pname))

def parse_args(args):
    if len(args) != 5:
        usage(args[0])
        sys.exit(1)
    else:
        return (args[1], args[2], args[3], args[4])

def main():
    # get config
    user, passwd, orgname, sfile = parse_args(sys.argv)

    # init Github SDK
    g = Github(user, passwd)

    with open(sfile, 'r') as fin:
            students = [line.strip() for line in fin]

    non_github = []
    for student in students:
            try:
                    s = g.get_user(student)
            except Exception:
                    #print("{} not a github member.".format(student))
                    non_github.append(student)
                    

    org = g.get_organization("williams-cs")
    members = org.get_members()
    logins = {member.login for member in members}
    non_org = []
    for student in students:
            if student not in members:
                    #print("{} not a member of {}.".format(student, orgname))
                    non_org.append(student)

    print("Not in github:")
    print(non_github)
    print("Not in {}:".format(orgname))
    print(non_org)

if __name__ == "__main__":
    main()
