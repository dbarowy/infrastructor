#!/usr/bin/env python

import sys
from subprocess import call

from config import Config


def main():
    # get config
    conf = Config(sys.argv)
    conf.pretty_print()

    # clone/update archive
    conf.pull_all(conf.archive_path, True, False)
    conf.pull_all(conf.submission_path, False, conf.anonymize_sub_path)

    # copy to TA folders
    conf.copy_to_ta_folders(conf.ta_path, conf.assignment_name,
                            conf.submission_path)

    ## set group permissions in submissions directory ... ##
    call(["chmod", "-R", "2770", conf.submission_path])

    ## in group permissions in TA directory ... ##
    ta = f"{conf.ta_path}/{conf.assignment_name}"
    call(["chmod", "-R", "2770", ta])


if __name__ == "__main__":
    main()
