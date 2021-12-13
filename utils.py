import re
import sys
from distutils import spawn

from typing import Sequence, Dict


def normalize(name: str) -> str:
    return re.sub(r"[^\w\s]", "_", name.lower())


def canonical_group_name(group: Sequence[str]) -> str:
    return "-".join(sorted(list(map(normalize, group))))


def group2repo(cname: str, aname: str, group: Sequence[str],
               format_string: str = "{}{}-{}") -> str:
    cname2 = normalize(cname)
    aname2 = normalize(aname)
    gname = canonical_group_name(group)
    return format_string.format(cname2, aname2, gname)


# stolen from: https://gist.github.com/hanleybrand/5224673
def java_string_hashcode(s: str) -> int:
    h = 0
    for c in s:
        h = (31 * h + ord(c)) & 0xFFFFFFFF
    return ((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000


def self_check() -> None:
    """
    Checks if `rsync` and `git` are in the PATH
    """
    if spawn.find_executable("rsync") is None:
        print("ERROR: Cannot find rsync.", file=sys.stderr)
        sys.exit(1)

    if spawn.find_executable("git") is None:
        print("ERROR: Cannot find git.", file=sys.stderr)
        sys.exit(1)


def round_robin_map(tas: Sequence[str], repos: Sequence[str]) -> Dict[str, str]:
    i = 0  # index into tas
    d: Dict[str, str] = {}  # map

    for r in repos:
        # assign TA to repository
        d[r] = tas[i]

        # advance TA index, wrapping if necessary
        i = i + 1
        if i >= len(tas):
            i = 0

    return d
