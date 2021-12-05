import datetime
import hashlib
import json
import os.path
import random
import sys
from typing import Dict, List

from utils import canonical_group_name, java_string_hashcode, round_robin_map


class Config(object):
    # config JSON
    # {
    #  "default_branch" : "master",
    #  "feedback_branch" : "TA-feedback",
    #  "hostname" : "github-wcs",
    #  "course" : "cs334",
    #  "assignment_name" : "hw0",
    #  "do_not_accept_changes_after_due_date_timestamp" : 1518671700,
    #                                                     # a UNIX timestamp
    #  "anonymize_sub_path" : true,
    #  "archive_path" : "/home/example/archive",
    #  "submission_path" : "/home/example/submission",
    #  "ta_path" : "/home/example/tas",
    #  "starter_repo" : "/home/example/starter-repo.git",
    #  "github_org" : "williams-cs",
    #  "TAs" : [ "ta_1", "ta_2", ..., "ta_n" ],
    #  "repository_map" : {
    #    "student_1" : "repo_1",
    #    "student_2" : "repo_2",
    #    ...
    #    "student_n" : "repo_n"
    #  }
    # }

    def __init__(self, json_conf_file: str):

        # open config file
        with open(json_conf_file, 'r') as f:
            # read config
            conf = json.loads(f.read())

        # declare/init fields
        self.hostname: str = conf["hostname"]
        self.user2repo: Dict[str, str] = {}
        self.repo2group: Dict[str, List[str]] = {}
        self.ta_assignments: Dict[str, str] = {}
        self.course: str = conf["course"]
        self.assignment_name: str = conf["assignment_name"]
        self.starter_repo: str = conf["starter_repo"]
        self.github_org: str = conf["github_org"]
        self.archive_path: str = conf["archive_path"]
        self.submission_path: str = conf["submission_path"]
        self.ta_path: str = conf["ta_path"]
        self.feedback_branch: str = conf["feedback_branch"]
        self.default_branch: str = conf["default_branch"] \
            if "default_branch" in conf else "main"
        if "do_not_accept_changes_after_due_date_timestamp" in conf:
            # TODO: type? best guess is str
            self.due_date = \
                conf["do_not_accept_changes_after_due_date_timestamp"]
        self.anonymize_sub_path: bool = conf["anonymize_sub_path"] \
            if "anonymize_sub_path" in conf else True
        self.rsync_excludes: List[str] = conf["rsync_excludes"]

        # populate mappings (user2repo, repo2group)
        for student in conf["repository_map"].keys():
            self.add_mapping(student, conf["repository_map"][student])

        # read TA list
        tas: List[str] = conf["TAs"]
        tas.sort()  # sorting ensures that TA order is deterministic

        # generate TA map
        random.seed(java_string_hashcode(conf["assignment_name"]))
        repos = self.repositories
        random.shuffle(repos)
        self.ta_assignments = round_robin_map(tas, repos)

    @property
    def list_of_users(self) -> List[str]:
        return list(self.user2repo.keys())

    def add_mapping(self, user: str, repo: str) -> None:
        # pair user with repo
        self.user2repo[user] = repo

        # pair repo with group
        # first, check to see if repo already in dict
        if repo in self.repo2group:
            # yes, so get existing group and add user
            group = self.repo2group[repo]
            group.append(user)
        else:
            # no, so add repo and new group from user
            self.repo2group[repo] = [user]

    def lookupGroup(self, repo: str) -> List[str]:
        return self.repo2group[repo]

    def lookupRepo(self, user: str) -> str:
        return self.user2repo[user]

    def pretty_print(self) -> None:
        print("Student -> repository map:")
        for user in self.user2repo.keys():
            print(f"  {user} -> {self.user2repo[user]}")

        print("TA -> repository map:")
        for repo in self.ta_assignments.keys():
            print(f"  {self.ta_assignments[repo]} -> {repo}")

        print(f"archive path: {self.archive_path}")
        print(f"submission path: {self.submission_path}")
        print(f"ta path: {self.ta_path}")
        print(f"course: {self.course}")
        print(f"assignment name: {self.assignment_name}")
        if hasattr(self, "do_not_accept_changes_after_due_date_timestamp"):
            print(f"""due date: {
            datetime.datetime.fromtimestamp(int(self.due_date))
                  .strftime('%Y-%m-%d %H:%M:%S')
            }""")
        print(f"feedback branch: {self.feedback_branch}")

    @property
    def repositories(self) -> List[str]:
        # sorting ensures that repository order is deterministic
        repos = list(self.repo2group.keys())
        return sorted(repos)

    def repo_ssh_path(self, repo: str) -> str:
        # return "git@" + self.hostname + ":" + self.github_org + "/" + repo + ".git"
        return f"git@{self.hostname}:{self.github_org}/{repo}.git"

    def lookupTA(self, repo: str) -> str:
        return self.ta_assignments[repo]

    def pull_path(self, basepath: str, repo: str, use_user_name: bool,
                  anonymize: bool) -> str:
        # if anonymize, then get the SHA1 hash of the repo name

        reponame = hashlib.sha1(repo.encode(
            'utf-8')).hexdigest() if anonymize else repo

        if use_user_name:
            group = self.lookupGroup(repo)
            gname = canonical_group_name(group)
            return os.path.join(basepath, gname, reponame)
        else:
            return os.path.join(basepath, reponame)

    # this method anonymizes the repository name
    def TA_target(self, ta_home: str, ta_dirname: str, repo: str) -> str:
        return os.path.join(ta_home, ta_dirname, self.lookupTA(repo),
                            hashlib.sha1(repo.encode('utf-8')).hexdigest())

    # yeah, we brute force these...
    # fortunately, there aren't many to check
    def deanonymize_sha1_repo(self, anonrepo: str) -> str:
        for repo in self.repo2group.keys():
            utf8_repo = repo.encode('utf-8')
            repohash = hashlib.sha1(utf8_repo).hexdigest()
            if anonrepo == repohash:
                return repo
        print("ERROR: Could not deanonymize repository with SHA1 = " + anonrepo)
        sys.exit(1)
