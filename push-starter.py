#!/usr/bin/env python

import sys
from config import Config


def main():
    # get config
    conf = Config(sys.argv)

    # issue go through the student repos, and add them as remotes for the
    # starter repo in the config. then push the master branch of the starter
    # repo to the student repo's master
    conf.push_starter()


if __name__ == "__main__":
    main()
