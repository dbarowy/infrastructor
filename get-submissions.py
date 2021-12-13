#!/usr/bin/env python

from subprocess import call

from Infrastructor import Infrastructor
from config import Config
from utils import self_check


def main() -> None:
    args = Infrastructor.default_parser.parse_args()

    # get config
    self_check()
    conf = Config(args.config, args.verbose)
    conf.pretty_print()

    # clone/update archive
    Infrastructor.pull_all(conf, conf.archive_path, True, False)
    Infrastructor.pull_all(conf, conf.submission_path, False,
                           conf.anonymize_sub_path)

    # copy to TA folders
    Infrastructor.copy_to_ta_folders(conf, conf.ta_path, conf.assignment_name,
                                     conf.submission_path)

    ## set group permissions in submissions directory ... ##
    call(["chmod", "-R", "2770", conf.submission_path])

    ## in group permissions in TA directory ... ##
    ta = f"{conf.ta_path}/{conf.assignment_name}"
    call(["chmod", "-R", "2770", ta])


if __name__ == "__main__":
    main()
