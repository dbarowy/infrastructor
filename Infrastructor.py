import errno
import os.path
import sys
from subprocess import call, Popen, PIPE
from typing import Dict, TypeVar

import argparse
from github.Organization import Organization

from config import Config

# Generics for type hints in merge_dicts()
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


# this makes a copy
def merge_dicts(base_dict: Dict[_KT, _VT], update_with: Dict[_KT, _VT]) -> Dict[
    _KT, _VT]:
    """Merges two dictionaries into a new dictionary.

    In the case of a conflict, the value in base_dict will be overwritten by
    value in update_with.

    :param base_dict: The base dictionary
    :param update_with: The dictionary to be updated with
    :return: A new dictionary that merges the content of two dictionary.
    """
    d = {}
    d.update(base_dict)
    d.update(update_with)
    return d


class Infrastructor(object):
    """The main class for Infrastructor

    Contains methods that takes Config class and executes logic
    """

    default_parser = argparse.ArgumentParser()
    """The default parser with the minimum required arguments

    ```python
    args = Infrastructor.default_parser.parse_args()
    conf = Config(args.config, args.verbose)
    ```
    """
    default_parser.add_argument('config', type=str,
                                help='config file for the lab')
    default_parser.add_argument('-v', '--verbose',
                                action='store_true',
                                help='enable verbose output')

    @staticmethod
    def pull_all(config: Config, basepath: str, use_user_name: bool,
                 anonymize: bool) -> None:
        """Pulls all repositories into archive and submission dirs

        :param config: The Config object for the assignment
        :param basepath: Pate to base directory
        :param use_user_name: Whether to use username as part of path
        :param anonymize: Whether to anonymize reponame
        """
        for repo in config.repositories:
            rpath = config.pull_path(basepath, repo, use_user_name, anonymize)
            if not os.path.exists(rpath):
                # clone it
                print(f"Cloning {config.repo_ssh_path(repo)} to {rpath}.")
                call(["git", "clone", config.repo_ssh_path(repo), rpath])
            else:  # existing repository
                # make sure we're on the default branch
                print(f"Switching to '{config.default_branch}' branch in "
                      f"{config.repo_ssh_path(repo)} at {rpath}")
                Popen(["git", "checkout", config.default_branch],
                      cwd=rpath).wait()  # note: blocking

                # first reset repository
                print(f"Resetting {config.repo_ssh_path(repo)} at {rpath}")
                Popen(["git", "checkout", "."],
                      cwd=rpath).wait()  # note: blocking

                # pull it
                print(f"Pulling {config.repo_ssh_path(repo)} in {rpath}")
                Popen(["git", "pull"], cwd=rpath).wait()  # note: blocking

            # if a due date was specified, roll back to due date
            if hasattr(config,
                       "do_not_accept_changes_after_due_date_timestamp"):
                proc = Popen(
                    ["git",
                     "rev-list",
                     "-1",
                     "--before=\"" + str(config.due_date) + "\"",
                     config.default_branch],
                    stdout=PIPE,
                    stderr=PIPE,
                    cwd=rpath
                )
                stdout, _ = proc.communicate()  # note: blocking
                pathspec = stdout.rstrip()
                Popen(["git",
                       "checkout",
                       pathspec],
                      cwd=rpath).wait()  # note: blocking

    @staticmethod
    def push_starter(config: Config) -> None:
        """Pushes the starter repo to all student repositories.

        Starter code is distributed by setting each student repository as a
        "remote" for the starter repository and then `push`ing.  Student
        repositories _must_ be empty (i.e., no `main` branch) otherwise
        `push` will fail.

        :param config: The Config object for the assignment
        """
        print(f"starter repo is: {config.starter_repo}")
        for repo in config.repositories:
            actual_repo = config.repo_ssh_path(repo)
            Popen(["git", "remote", "add", repo, actual_repo],
                  cwd=config.starter_repo).wait()
            Popen(["git", "push", repo, config.default_branch],
                  cwd=config.starter_repo).wait()

    @staticmethod
    def copy_to_ta_folders(config: Config, ta_home: str, ta_dirname: str,
                           basepath: str) -> None:
        """ Copies all local repositories to TA directories for grading

        :param config: The Config object for the assignment
        :param ta_home: Path to home directory for all TA grading
        :param ta_dirname: Name of directory for this assignment
        :param basepath: Base path where local repositories are stored
        """
        # keep track of repository -> TA map and print out the key
        # after doing all of the copying
        ta_map = []

        # cp all files except git stuff and other junk
        for repo in config.repositories:
            # compute target
            target = config.TA_target(ta_home, ta_dirname, repo)

            # save mapping
            ta_map.append((repo, target))

            if not os.path.exists(target):
                os.makedirs(target)
            # compute source; add slash so that rsync copies
            # _contents_ of folder into target
            source = config.pull_path(
                basepath, repo, False, config.anonymize_sub_path) + "/"

            # copy to ta folder
            if config.verbose:
                print(f"Copying from {source} to {target}")
            cmd = ["rsync",
                   "-vurlptoD" if config.verbose else "-urlptoD"]
            cmd.extend([f"--exclude={e}" for e in config.rsync_excludes])
            cmd.extend([source, target])
            call(cmd)
        # print mappings
        for (repo, target) in ta_map:
            print(repo + " -> " + target)

    @staticmethod
    def copy_from_ta_folders(config: Config, ta_home: str,
                             ta_dirname: str, basepath: str) -> None:
        """ Copies all local repositories back from TA directories after grading

        :param config: The Config object for the assignment
        :param ta_home: Path to home directory for all TA grading
        :param ta_dirname: Name of directory for this assignment
        :param basepath: Base path for local repositories to be copied to
        """
        # cp all files except git stuff
        for repo in config.repositories:
            # compute target
            target = config.pull_path(
                basepath, repo, False, config.anonymize_sub_path)
            # compute source; trailing slash is to force rsync to copy the
            # CONTENTS of source dir into the target dir, not to copy source
            # dir into the target dir
            source = config.TA_target(ta_home, ta_dirname, repo) + "/"
            if not os.path.exists(target):
                # abort if target directory is missing!
                print(f"ERROR: Target submission directory {target} "
                      f"is missing! Aborting.", file=sys.stderr)
                sys.exit(1)
                # os.makedirs(target)
            # copy to ta folder
            if config.verbose:
                print(f"Copying from {source} to {target}")
            call(
                ["rsync",
                 # changed flags to maintain permissions
                 "-vurlptoD" if config.verbose else "-urlptoD",
                 "--exclude=*/.git",
                 "--exclude=*/.gitignore",
                 "--exclude=*/*.class",
                 source,
                 target]
            )

    @staticmethod
    def branch_exists(config: Config, rdir: str) -> bool:
        """Checks if the feedback branch exists in a local repository

        :param config: The Config object for the assignment
        :param rdir: Path to a local repository
        :return: If the feedback branch exists.
        """
        # check to see if FEEDBACK_BRANCH branch exists
        proc = Popen(["git", "show-ref", "--verify", "--quiet",
                      "refs/heads/" + config.feedback_branch],
                     stdout=PIPE,
                     stderr=PIPE,
                     cwd=rdir)
        proc.communicate()  # note: blocking; don't care about output
        return proc.returncode == 0

    @staticmethod
    def commit_changes(config: Config, basepath: str) -> None:
        """Commits changes to the feedback branch in all repos

        :param config: The Config object for the assignment
        :param basepath: basepath for local path of repositories
        """
        for repo in config.repositories:
            # get submissions dir path for repo
            rdir = config.pull_path(basepath, repo, False,
                                    config.anonymize_sub_path)
            if not Infrastructor.branch_exists(config, rdir):
                # create branch
                if config.verbose:
                    print(f"Creating new branch {config.feedback_branch}")
                Popen(["git", "checkout", "-b", config.feedback_branch],
                      cwd=rdir).wait()
            else:
                Popen(["git", "checkout", config.feedback_branch],
                      cwd=rdir).wait()
            # add any new files
            if config.verbose:
                print(f"Adding any new files in {rdir}")
            Popen(["git", "add", "*"], cwd=rdir).wait()  # note: blocking
            # commit
            if config.verbose:
                print("Committing feedback for " + rdir)
            Popen(["git", "commit", "-am", "TA feedback"],
                  cwd=rdir).wait()  # note: blocking

    @staticmethod
    def issue_pull_request(config: Config, reponame: str,
                           org: Organization) -> int:
        """Push local feedback branch to remote and issue pull request to the
        default branch for the specified repo

        :param config: The Config object for the assignment
        :param reponame: Name of the repository
        :param org: A github.Organization object
        :return: an error number defined in errno; or 0 if no error.
        """
        # extract basename
        bn = os.path.basename(reponame)

        # get real repository name if hashed
        repo = config.deanonymize_sha1_repo(bn) \
            if config.anonymize_sub_path else bn

        # get submissions dir path for repo
        rdir = config.pull_path(config.submission_path, reponame, False, False)

        # obtain handle to remote repository
        grepo = org.get_repo(repo)

        # ensure that the default branch exists on remote
        remote_branches = []
        for rb in grepo.get_branches():
            remote_branches.append(rb.name)

        if config.default_branch not in remote_branches:
            print(f"ABORT: {config.default_branch} branch does not exist in remote repository.")
            return errno.ENOENT

        if config.feedback_branch in remote_branches:
            print(f"ABORT: {config.feedback_branch} branch already exists in "
                  f"remote repository.")
            return errno.EEXIST

        if config.verbose:
            print(f"Pushing branch {config.feedback_branch} to origin.")

        #### Lida: needed to edit since reponame contains the relative path, not just the name ####
        # Dan/Bill: not sure why this is necessary... hopefully we trigger it again and figure out why...
        # Popen(["git", "push", "origin", self.feedback_branch], cwd=reponame).wait()
        Popen(["git", "push", "origin", config.feedback_branch],
              cwd=rdir).wait()

        # create pull request
        if config.verbose:
            print(f"Issuing pull request from branch '{config.feedback_branch}"
                  f"' to branch '{config.default_branch}' in {repo}.")

        # push commits upstream

        # we get the repo name from github so that you can run
        # this command from other locations
        grepo = org.get_repo(os.path.basename(repo))
        grepo.create_pull(
            title="Feedback",
            base=config.default_branch,
            head=config.feedback_branch,
            body="Feedback on " + config.assignment_name +
                 " from " + config.course + " teaching staff."
        )
        return 0
