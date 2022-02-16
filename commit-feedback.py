#!/usr/bin/env python3

import sys

from Infrastructor import Infrastructor
from config import Config
from utils import self_check


def main() -> None:
    args = Infrastructor.default_parser.parse_args()

    # get config
    self_check()
    conf = Config(args.config, args.verbose)


# copy every commented assignment from TA location to submissions folder
    Infrastructor.copy_from_ta_folders(conf, conf.ta_path, conf.assignment_name,
                                       conf.submission_path)

    # commit changes
    Infrastructor.commit_changes(conf, conf.submission_path)


if __name__ == "__main__":
    main()
