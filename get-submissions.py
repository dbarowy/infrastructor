#!/usr/bin/env python

import sys
from subprocess import call

from Infrastructor import Infrastructor


def main() -> None:
    # get config
    infra = Infrastructor(sys.argv)
    conf = infra.config
    conf.pretty_print()

    # clone/update archive
    infra.pull_all(conf, conf.archive_path, True, False)
    infra.pull_all(conf, conf.submission_path, False, conf.anonymize_sub_path)

    # copy to TA folders
    infra.copy_to_ta_folders(conf, conf.ta_path, conf.assignment_name,
                             conf.submission_path)

    ## set group permissions in submissions directory ... ##
    call(["chmod", "-R", "2770", conf.submission_path])

    ## in group permissions in TA directory ... ##
    ta = f"{conf.ta_path}/{conf.assignment_name}"
    call(["chmod", "-R", "2770", ta])


if __name__ == "__main__":
    main()
