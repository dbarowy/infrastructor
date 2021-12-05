#!/usr/bin/env python

import sys

from Infrastructor import Infrastructor


def main() -> None:
    # get config
    infra = Infrastructor(sys.argv)
    conf = infra.config

    # copy every commented assignment from TA location to submissions folder
    infra.copy_from_ta_folders(conf, conf.ta_path, conf.assignment_name,
                               conf.submission_path)

    # commit changes
    infra.commit_changes(conf, conf.submission_path)


if __name__ == "__main__":
    main()
