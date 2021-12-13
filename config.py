import datetime
import hashlib
import json
import os.path
import random
import sys
from typing import Dict, List

from utils import canonical_group_name, java_string_hashcode, round_robin_map


class Config(object):
    """
    A data-only class storing the parsed Infrastructor configuration for an
    assignment

    This class reads in an Infrastructor JSON configuration file with a
    specified path and parses them into a list of

    config JSON should be in the following format
    ```json
    {
     "default_branch" : "master",
     "feedback_branch" : "TA-feedback",
     "hostname" : "github-wcs",
     "course" : "cs334",
     "assignment_name" : "hw0",
     "do_not_accept_changes_after_due_date_timestamp" : 1518671700,
                                                        # a UNIX timestamp
     "anonymize_sub_path" : true,
     "archive_path" : "/home/example/archive",
     "submission_path" : "/home/example/submission",
     "ta_path" : "/home/example/tas",
     "starter_repo" : "/home/example/starter-repo.git",
     "github_org" : "williams-cs",
     "TAs" : [ "ta_1", "ta_2", ..., "ta_n" ],
     "repository_map" : {
       "student_1" : "repo_1",
       "student_2" : "repo_2",
       ...
       "student_n" : "repo_n"
     }
    }
    ```

    Attributes:
        hostname (str): The name of your SSH `config` host to use for script interaction. This allows you to use a different GitHub identity for managing course scripts because, presently, PyGithub does not support two-factor authentication.
        user2repo (Dict[str, str]): A dictionary mapping user to their repository name.
        repo2group (Dict[str, List[str]]): A dictionary mapping repo name to the list of students (assuming group assignment). The list will be length 1 if individual assignment.
        ta_assignments (Dict[str, str]): A dictionary mapping each repository to the grading TAs.
        course (str): The name of the course.
        assignment_name (str): The name of the assignment
        starter_repo (str): Path to starter repo.  Starter code is distributed by setting each student repository as a "remote" for the starter repository and then `push`ing.  Student repositories _must_ be empty (i.e., no `main` branch) otherwise `push` will fail.
        github_org (str): Name of the GitHub organization to use.
        archive_path (str): Path to folder intended as deanonymized repository of student submissions for Academic Honor Code cases.
        submission_path (str): Path to faculty-only staging area for squashing and modifying TA feedback before issuing pull requests.
        ta_path (str): Path to TA staging area where anonymized student submissions are copied.
        feedback_branch (str): Branch to commit TA/instructor feedback on. Pull requests are issued from this branch.
        default_branch (str): Branch that student commits to. Defaults to `main` if not specified.
        due_date (int): Optional. a UNIX timestamp representing the due date in the local timezone.
        anonymize_sub_path (bool): whether the contents of the `submissions` folder, which is viewable only by faculty (not TAs), is anonymized.
        rsync_excludes (List[str]): List of files & directories to be excluded from rsync when copying to TA folder.
    """

    def __init__(self, json_conf_file: str, verbosity: bool):

        # open config file
        with open(json_conf_file, 'r') as f:
            # read config
            conf = json.loads(f.read())

        # declare/init fields

        self.verbose: bool = verbosity
        "Flag to enable verbose output"

        self.hostname: str = conf["hostname"]
        """
        The name of your SSH `config` host to use for script
        interaction. This allows you to use a different GitHub identity for
        managing course scripts because, presently, PyGithub does not support
        two-factor authentication.
        """

        self.user2repo: Dict[str, str] = {}
        "A dictionary mapping user to their repository name."

        self.repo2group: Dict[str, List[str]] = {}
        """A dictionary mapping repo name to the list of students (assuming
        group assignment). The list will be length 1 if individual assignment.
        """

        self.ta_assignments: Dict[str, str] = {}
        "A dictionary mapping each repository to the grading TAs."

        self.course: str = conf["course"]
        "The name of the course."

        self.assignment_name: str = conf["assignment_name"]
        "The name of the assignment."

        self.starter_repo: str = conf["starter_repo"]
        """
        Path to starter repo.  Starter code is distributed by setting each
        student repository as a "remote" for the starter repository and then
        `push`ing.  Student repositories _must_ be empty (i.e., no `main`
        branch) otherwise `push` will fail.
        """

        self.github_org: str = conf["github_org"]
        "Name of the GitHub organization to use."

        self.archive_path: str = conf["archive_path"]
        """Path to folder intended as deanonymized repository of student
        submissions for Academic Honor Code cases."""

        self.submission_path: str = conf["submission_path"]
        """Path to faculty-only staging area for squashing and modifying TA
        feedback before issuing pull requests."""

        self.ta_path: str = conf["ta_path"]
        """Path to TA staging area where anonymized student submissions are
        copied."""

        self.feedback_branch: str = conf["feedback_branch"]
        """Branch to commit TA/instructor feedback on. Pull requests are
        issued from this branch."""

        self.default_branch: str = conf["default_branch"] \
            if "default_branch" in conf else "main"
        "Branch that student commits to. Defaults to `main` if not specified."

        if "do_not_accept_changes_after_due_date_timestamp" in conf:
            # TODO: type? best guess is int
            self.due_date = \
                conf["do_not_accept_changes_after_due_date_timestamp"]
            "A UNIX timestamp representing the due date in the local timezone."

        self.anonymize_sub_path: bool = conf["anonymize_sub_path"] \
            if "anonymize_sub_path" in conf else True
        """ whether the contents of the `submissions` folder, which is viewable
        only by faculty (not TAs), is anonymized."""

        self.rsync_excludes: List[str] = conf["rsync_excludes"]
        """List of files & directories to be excluded from rsync when copying
        to TA folder."""

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
        """Returns a list of all users in the course

        :rtype: List[str]
        :return: a list of all users in the course
        """
        return list(self.user2repo.keys())

    def add_mapping(self, user: str, repo: str) -> None:
        """An internal method used to initialize self.user2repo and
        self.repo2group attributes

        :param user: Name of student
        :param repo: Name of repository
        """

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
        """Looks up the student(s) assigned to the repo

        :param repo: Name of the repository
        :rtype: List[str]
        :return: A list of users assigned to the repo
        """
        return self.repo2group[repo]

    def lookupRepo(self, user: str) -> str:
        """Looks up the repository the user is assigned to

        :param user: Name of the user
        :rtype: str
        :return: Name of the repository
        """
        return self.user2repo[user]

    def pretty_print(self) -> None:
        """Prints out a human-readable representation of the configuration"""
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
        """Returns a list of sorted repositories of this assignment

        :rtype: List[str]
        :return: A list of sorted repositories of this assignment
        """
        # sorting ensures that repository order is deterministic
        repos = list(self.repo2group.keys())
        return sorted(repos)

    def repo_ssh_path(self, repo: str) -> str:
        """Returns the Git SSH path of a given repo

        :param repo: Name of the repo
        :rtype: str
        :return: Git SSH path of a given repository
        """
        return f"git@{self.hostname}:{self.github_org}/{repo}.git"

    def lookupTA(self, repo: str) -> str:
        """Looks up the TA assigned to grade the repo

        :param repo: Name of the repo
        :rtype: Name of the TA
        :return: Name of the TA assigned to grade the repo
        """
        return self.ta_assignments[repo]

    def pull_path(self, basepath: str, repo: str, use_user_name: bool,
                  anonymize: bool) -> str:
        """Finds out the local path for the repository

        :param basepath: basepath for local path (depending on category)
        :param repo: Name of the repository
        :param use_user_name: Whether user name is part of the path
        :param anonymize: Whether reponame is anonymized
        :return: The local path of the specified repository
        """
        # if anonymize, then get the SHA1 hash of the repo name

        reponame = hashlib.sha1(repo.encode(
            'utf-8')).hexdigest() if anonymize else repo

        if use_user_name:
            group = self.lookupGroup(repo)
            gname = canonical_group_name(group)
            return os.path.join(basepath, gname, reponame)
        else:
            return os.path.join(basepath, reponame)

    def TA_target(self, ta_home: str, ta_dirname: str, repo: str) -> str:
        """Finds out the anonymized local TA path of a repo.

        Note that this method anonymizes the repository name.

        :param ta_home: Path to home directory for all TA grading
        :param ta_dirname: Name of directory for this assignment
        :param repo: Name of the repository
        :return: The anonymized local TA path of a repo
        """
        return os.path.join(ta_home, ta_dirname, self.lookupTA(repo),
                            hashlib.sha1(repo.encode('utf-8')).hexdigest())

    def deanonymize_sha1_repo(self, anonrepo: str) -> str:
        """Returns the deanonymized name of a repository

        yeah, we brute force these...
        fortunately, there aren't many to check

        :param anonrepo: The anonymized SHA1 name of the repo
        :return: the deanonymized name of a repository
        """
        for repo in self.repo2group.keys():
            utf8_repo = repo.encode('utf-8')
            repohash = hashlib.sha1(utf8_repo).hexdigest()
            if anonrepo == repohash:
                return repo
        print("ERROR: Could not deanonymize repository with SHA1 = " + anonrepo)
        sys.exit(1)
