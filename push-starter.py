#!/usr/bin/env python

import sys

from Infrastructor import Infrastructor


def main() -> None:
    # get config
    infra = Infrastructor(sys.argv)
    conf = infra.config

    # issue go through the student repos, and add them as remotes for the
    # starter repo in the config. then push the default branch of the starter
    # repo to the student repo's default branch
    infra.push_starter(conf)


if __name__ == "__main__":
    main()
