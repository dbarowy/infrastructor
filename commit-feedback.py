#!/usr/bin/env python

import sys

from config import Config


def main() -> None:
    # get config
    conf = Config(sys.argv)

    # copy every commented assignment from TA location to submissions folder
    conf.copy_from_ta_folders(conf.ta_path, conf.assignment_name,
                              conf.submission_path)

    # commit changes
    conf.commit_changes(conf.submission_path)


if __name__ == "__main__":
    main()
