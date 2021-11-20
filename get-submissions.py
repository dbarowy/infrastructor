#!/usr/bin/env python

import sys
from config import Config
from subprocess import call


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
    ta = "%s/%s" % (conf.ta_path, conf.assignment_name)
    call(["chmod", "-R", "2770", ta])


if __name__ == "__main__":
    main()
