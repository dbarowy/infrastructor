#!/usr/bin/env python

import sys

from Infrastructor import Infrastructor
from config import Config
from utils import self_check


def main() -> None:
    # get config
    args = Infrastructor.default_parser.parse_args()
    self_check()
    conf = Config(args.config, args.verbose)


    # issue go through the student repos, and add them as remotes for the
    # starter repo in the config. then push the default branch of the starter
    # repo to the student repo's default branch
    Infrastructor.push_starter(conf)


if __name__ == "__main__":
    main()
