import datetime
import errno
import hashlib
import os.path
import sys
from subprocess import call, Popen, PIPE
from typing import Any, Dict, List, Sequence, TypeVar

from github.Organization import Organization

from config import Config
from utils import canonical_group_name, self_check

# Generics for type hints in merge_dicts()
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


# this makes a copy
def merge_dicts(base_dict: Dict[_KT, _VT], update_with: Dict[_KT, _VT]) -> Dict[_KT, _VT]:
    d = {}
    d.update(base_dict)
    d.update(update_with)
    return d


class Infrastructor(object):
    def argparse(self, args: Sequence[str]) -> Dict[str, Any]:
        pname = os.path.basename(args[0])
        # convert to list and strip program name
        # xs = list(args)
        tail = args[1:]
        return self.rec_argparse(tail, pname)

    def rec_argparse(self, args: Sequence[str], pname: str) -> Dict[str, Any]:
        flags = {
            "-v": lambda: {"verbose": True}
        }

        # base case 1: zero-length string
        if len(args) == 0:
            Infrastructor.usage(pname)
            sys.exit(1)

        # base case 2: string has one (positional) argument left
        if len(args) == 1:
            return {
                "json_conf_file": args[0],
                "verbose": False
            }
        # recursive case: optional flags remain
        else:
            print("length >1 arg", file=sys.stderr)
            try:
                head, tail = args[0], args[1:]
                d = flags[head]()
                return merge_dicts(self.rec_argparse(tail, pname), d)
            except Exception:
                Infrastructor.usage(pname)
                sys.exit(1)

    def __init__(self, args: Sequence[str]):
        print(args)
        # self check
        self_check()

        # get arguments
        opts = self.argparse(args)
        self.verbose: bool = opts["verbose"]

        self.config = Config(opts["json_conf_file"])

    @staticmethod
    def usage(pname: str) -> None:
        print(f"Usage: {pname} [flags] <json config file>", file=sys.stderr)
        print("\twhere flags are:", file=sys.stderr)
        print("\t-v\tverbose mode; print debug output.", file=sys.stderr)

    @staticmethod
    def list_of_users(config: Config) -> List[str]:
        return list(config.user2repo.keys())

    @staticmethod
    def lookupGroup(config: Config, repo: str) -> List[str]:
        return config.repo2group[repo]

    @staticmethod
    def lookupRepo(config: Config, user: str) -> str:
        return config.user2repo[user]

    @staticmethod
    def pretty_print(config: Config) -> None:
        print("Student -> repository map:")
        for user in config.user2repo.keys():
            print(f"  {user} -> {config.user2repo[user]}")

        print("TA -> repository map:")
        for repo in config.ta_assignments.keys():
            print(f"  {config.ta_assignments[repo]} -> {repo}")

        print(f"archive path: {config.archive_path}")
        print(f"submission path: {config.submission_path}")
        print(f"ta path: {config.ta_path}")
        print(f"course: {config.course}")
        print(f"assignment name: {config.assignment_name}")
        if hasattr(config, "do_not_accept_changes_after_due_date_timestamp"):
            print(f"""due date: {
            datetime.datetime.fromtimestamp(int(config.due_date))
                  .strftime('%Y-%m-%d %H:%M:%S')
            }""")
        print(f"feedback branch: {config.feedback_branch}")

    @staticmethod
    def repositories(config: Config) -> List[str]:
        # sorting ensures that repository order is deterministic
        repos = list(config.repo2group.keys())
        return sorted(repos)

    @staticmethod
    def repo_ssh_path(config: Config, repo: str) -> str:
        # return "git@" + config.hostname + ":" + config.github_org + "/" + repo + ".git"
        return f"git@{config.hostname}:{config.github_org}/{repo}.git"

    @staticmethod
    def lookupTA(config: Config, repo: str) -> str:
        return config.ta_assignments[repo]

    @staticmethod
    def pull_path(config: Config, basepath: str, repo: str,
                  use_user_name: bool,
                  anonymize: bool) -> str:
        # if anonymize, then get the SHA1 hash of the repo name

        reponame = hashlib.sha1(repo.encode(
            'utf-8')).hexdigest() if anonymize else repo

        if use_user_name:
            group = Infrastructor.lookupGroup(config, repo)
            gname = canonical_group_name(group)
            return os.path.join(basepath, gname, reponame)
        else:
            return os.path.join(basepath, reponame)

    # this method anonymizes the repository name
    @staticmethod
    def TA_target(config: Config, ta_home: str, ta_dirname: str,
                  repo: str) -> str:
        return os.path.join(ta_home, ta_dirname,
                            Infrastructor.lookupTA(config, repo),
                            hashlib.sha1(repo.encode('utf-8')).hexdigest())

    @staticmethod
    def pull_all(config: Config, basepath: str, use_user_name: bool,
                 anonymize: bool) -> None:
        # pull all repositories into archive and submission dirs
        for repo in Infrastructor.repositories(config):
            rpath = Infrastructor.pull_path(config, basepath, repo,
                                   use_user_name, anonymize)
            if not os.path.exists(rpath):
                # clone it
                print(f"Cloning {Infrastructor.repo_ssh_path(config, repo)} to {rpath}.")
                call(["git", "clone", Infrastructor.repo_ssh_path(config, repo), rpath])
            else:
                # pull it
                print(f"Pulling {Infrastructor.repo_ssh_path(config, repo)} to {rpath}")
                Popen(["git", "pull"], cwd=rpath).wait()  # note: blocking

            # if a due date was specified, roll back to due date
            if hasattr(config, "do_not_accept_changes_after_due_date_timestamp"):
                proc = Popen(
                    ["git",
                     "rev-list",
                     "-1",
                     "--before=\"" + str(config.due_date) + "\"", "master"],
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

    def push_starter(self, config: Config) -> None:
        print(f"starter repo is: {config.starter_repo}")
        for repo in self.repositories(config):
            actual_repo = self.repo_ssh_path(config, repo)
            Popen(["git", "remote", "add", repo, actual_repo],
                  cwd=config.starter_repo).wait()
            Popen(["git", "push", repo, "master"],
                  cwd=config.starter_repo).wait()

    def copy_to_ta_folders(self, config: Config, ta_home: str, ta_dirname: str,
                           basepath: str) -> None:
        # keep track of repository -> TA map and print out the key
        # after doing all of the copying
        ta_map = []

        # cp all files except git stuff and other junk
        for repo in Infrastructor.repositories(config):
            # compute target
            target = Infrastructor.TA_target(config, ta_home, ta_dirname, repo)

            # save mapping
            ta_map.append((repo, target))

            if not os.path.exists(target):
                os.makedirs(target)
            # compute source; add slash so that rsync copies
            # _contents_ of folder into target
            source = Infrastructor.pull_path(config, basepath, repo, False,
                                    config.anonymize_sub_path) + "/"

            # copy to ta folder
            if self.verbose:
                print(f"Copying from {source} to {target}")
            cmd = ["rsync",
                   "-vurlptoD" if self.verbose else "-urlptoD"]
            cmd.extend([f"--exclude={e}" for e in config.rsync_excludes])
            cmd.extend([source, target])
            call(cmd)
        # print mappings
        for (repo, target) in ta_map:
            print(repo + " -> " + target)

    def copy_from_ta_folders(self, config: Config, ta_home: str,
                             ta_dirname: str, basepath: str) -> None:
        # cp all files except git stuff
        for repo in Infrastructor.repositories(config):
            # compute target
            target = Infrastructor.pull_path(
                config,
                basepath, repo, False, config.anonymize_sub_path)
            # compute source; trailing slash is to force rsync to copy the
            # CONTENTS of source dir into the target dir, not to copy source
            # dir into the target dir
            source = Infrastructor.TA_target(config, ta_home, ta_dirname, repo) + "/"
            if not os.path.exists(target):
                # abort if target directory is missing!
                print(f"ERROR: Target submission directory {target} "
                      f"is missing! Aborting.", file=sys.stderr)
                sys.exit(1)
                # os.makedirs(target)
            # copy to ta folder
            if self.verbose:
                print(f"Copying from {source} to {target}")
            call(
                ["rsync",
                 # changed flags to maintain permissions
                 "-vurlptoD" if self.verbose else "-urlptoD",
                 "--exclude=*/.git",
                 "--exclude=*/.gitignore",
                 "--exclude=*/*.class",
                 source,
                 target]
            )

    @staticmethod
    def branch_exists(config: Config, rdir: str) -> bool:
        # check to see if FEEDBACK_BRANCH branch exists
        proc = Popen(["git", "show-ref", "--verify", "--quiet",
                      "refs/heads/" + config.feedback_branch],
                     stdout=PIPE,
                     stderr=PIPE,
                     cwd=rdir)
        proc.communicate()  # note: blocking; don't care about output
        return proc.returncode == 0

    def commit_changes(self, config: Config, basepath: str) -> None:
        for repo in Infrastructor.repositories(config):
            # get submissions dir path for repo
            rdir = Infrastructor.pull_path(config, basepath, repo, False,
                                  config.anonymize_sub_path)
            if not Infrastructor.branch_exists(config, rdir):
                # create branch
                if self.verbose:
                    print(f"Creating new branch {config.feedback_branch}")
                Popen(["git", "checkout", "-b", config.feedback_branch],
                      cwd=rdir).wait()
            else:
                Popen(["git", "checkout", config.feedback_branch],
                      cwd=rdir).wait()
            # add any new files
            if self.verbose:
                print(f"Adding any new files in {rdir}")
            Popen(["git", "add", "*"], cwd=rdir).wait()  # note: blocking
            # commit
            if self.verbose:
                print("Committing feedback for " + rdir)
            Popen(["git", "commit", "-am", "TA feedback"],
                  cwd=rdir).wait()  # note: blocking

    # yeah, we brute force these...
    # fortunately, there aren't many to check
    @staticmethod
    def deanonymize_sha1_repo(config: Config, anonrepo: str) -> str:
        for repo in config.repo2group.keys():
            utf8_repo = repo.encode('utf-8')
            repohash = hashlib.sha1(utf8_repo).hexdigest()
            if anonrepo == repohash:
                return repo
        print("ERROR: Could not deanonymize repository with SHA1 = " + anonrepo)
        sys.exit(1)

    def issue_pull_request(self, config: Config, reponame: str,
                           org: Organization) -> int:
        # extract basename
        bn = os.path.basename(reponame)

        # get real repository name if hashed
        repo = Infrastructor.deanonymize_sha1_repo(config, bn) \
            if config.anonymize_sub_path else bn

        # get submissions dir path for repo
        rdir = Infrastructor.pull_path(
            config, config.submission_path, reponame, False, False)

        # obtain handle to remote repository
        grepo = org.get_repo(repo)

        # ensure that the master branch exists on remote
        remote_branches = []
        for rb in grepo.get_branches():
            remote_branches.append(rb.name)

        if "master" not in remote_branches:
            print("ABORT: master branch does not exist in remote repository.")
            return errno.ENOENT

        if config.feedback_branch in remote_branches:
            print(f"ABORT: {config.feedback_branch} branch already exists in "
                  f"remote repository.")
            return errno.EEXIST

        if self.verbose:
            print(f"Pushing branch {config.feedback_branch} to origin.")

        #### Lida: needed to edit since reponame contains the relative path, not just the name ####
        # Dan/Bill: not sure why this is necessary... hopefully we trigger it again and figure out why...
        # Popen(["git", "push", "origin", self.feedback_branch], cwd=reponame).wait()
        Popen(["git", "push", "origin", config.feedback_branch],
              cwd=rdir).wait()

        # create pull request
        if self.verbose:
            print(
                f"Issuing pull request from branch '{config.feedback_branch}' "
                f"to branch 'master' in {repo}.")

        # push commits upstream

        # we get the repo name from github so that you can run
        # this command from other locations
        grepo = org.get_repo(os.path.basename(repo))
        grepo.create_pull(
            title="Feedback",
            base="master",
            head=config.feedback_branch,
            body="Feedback on " + config.assignment_name +
                 " from " + config.course + " teaching staff."
        )
        return 0
