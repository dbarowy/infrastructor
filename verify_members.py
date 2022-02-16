#!/usr/bin/env python3

import argparse

from github import Github


def main() -> None:
    # get config
    parser = argparse.ArgumentParser()
    parser.add_argument("user", type=str,
                        help="github username")
    parser.add_argument("password", type=str,
                        help="github password")
    parser.add_argument('orgname', type=str,
                        help='org name')
    parser.add_argument('sfile', type=str,
                        help='student file')
    args = parser.parse_args()

    # init Github SDK
    g = Github(args.user, args.password)

    with open(args.sfile, 'r') as fin:
        students = [line.strip() for line in fin]

    non_github = []
    for student in students:
        try:
            s = g.get_user(student)
        except Exception:
            # print(f"{student} not a github member.")
            non_github.append(student)

    org = g.get_organization("williams-cs")
    members = org.get_members()
    logins = {member.login for member in members}
    non_org = []
    for student in students:
        if student not in members:
            # print(f"{student} not a member of {orgname}.")
            non_org.append(student)

    print("Not in github:")
    print(non_github)
    print(f"Not in {args.orgname}:")
    print(non_org)


if __name__ == "__main__":
    main()
