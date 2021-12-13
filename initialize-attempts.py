#!/usr/bin/env python

from urllib.parse import urljoin

import argparse
from requests.auth import HTTPBasicAuth

from Infrastructor import Infrastructor
from config import Config
from utils import self_check


def main() -> None:
    # get config
    parser = argparse.ArgumentParser(
        description='Pass in a list of Infrastructor configs to Attempt API '
                    'Server for initialization.')

    parser.add_argument('user', type=str,
                        help='username for attempt server')
    parser.add_argument('password', type=str,
                        help='password for attempt server')

    parser.add_argument('config', type=str,
                        help='a list of config files for labs', nargs="+")

    parser.add_argument('--attempt_server', type=str,
                        default='http://localhost:8080',
                        help='address and port for attempt server. e.g. '
                             '"http://localhost:8080"')
    parser.add_argument('--api_uri', type=str, default='/admin/lab/add',
                        help='URI of the API. e.g. "/admin/lab/add"')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='enable verbose output')

    args = parser.parse_args()

    self_check()
    conf = [Config(c, args.verbose) for c in args.config]

    full_api_uri: str = urljoin(args.attempt_server, args.api_uri)
    auth = HTTPBasicAuth(args.user, args.password)
    Infrastructor.initialize_attempt_counter(conf, full_api_uri, auth)


if __name__ == "__main__":
    main()
