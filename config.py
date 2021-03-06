

import errno
import sys
import os.path
import re
import random
import json
import hashlib
import datetime
from subprocess import call, Popen, PIPE
from shutil import copyfile
from distutils import spawn
from optparse import OptionParser
from github import Github

# this makes a copy
def merge_dicts(base_dict, update_with):
    d = {}
    d.update(base_dict)
    d.update(update_with)
    return d

class Config(object):
    # config JSON
    # {
    #  "feedback_branch" : "TA-feedback",
    #  "hostname" : "github-wcs",
    #  "course" : "cs334",
    #  "assignment_name" : "hw0",
    #  "do_not_accept_changes_after_due_date_timestamp" : 1518671700, # a UNIX timestamp
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

    def normalize(name):
        return re.sub(r"[^\w\s]", "_", name.lower())

    def canonical_group_name(group):
        return "-".join(sorted(list(map(Config.normalize, group))))

    def group2repo(cname, aname, group, format_string="{}{}-{}"):
        cname2 = Config.normalize(cname)
        aname2 = Config.normalize(aname)
        gname = Config.canonical_group_name(group)
        return format_string.format(cname2, aname2, gname)

    # stolen from: https://gist.github.com/hanleybrand/5224673
    def java_string_hashcode(s):
        h = 0
        for c in s:
            h = (31 * h + ord(c)) & 0xFFFFFFFF
        return ((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000

    def usage(self, pname):
        print("Usage: {0} [flags] <json config file>".format(pname),
              file=sys.stderr)
        print("\twhere flags are:", file=sys.stderr)
        print("\t-v\tverbose mode; print debug output.", file=sys.stderr)

    def argparse(self, args):
        pname = os.path.basename(args[0])
        # convert to list and strip program name
        xs = list(args)
        tail = args[1:]
        return self.rec_argparse(tail, pname)

    def rec_argparse(self, args, pname):
        flags = {
            "-v" : lambda: { "verbose" : True }
        }

        # base case 1: zero-length string
        if len(args) == 0:
            self.usage(pname)
            sys.exit(1)

        # base case 2: string has one (positional) argument left
        if len(args) == 1:
            return {
                "json_conf_file" : args[0],
                "verbose" : False
            }
        # recursive case: optional flags remain
        else:
            print("length >1 arg", file=sys.stderr)
            try:
                head, tail = args[0], args[1:]
                d = flags[head]()
                return merge_dicts(self.rec_argparse(tail, pname), d)
            except:
                self.usage(pname)
                sys.exit(1)

    def __init__(self, args):
        print(args)
        # self check
        self.self_check()

        # get arguments
        opts = self.argparse(args)

        # open config file
        with open(opts["json_conf_file"], 'r') as f:
            # read config
            conf = json.loads(f.read())

        # declare/init fields
        self.hostname = conf["hostname"]
        self.verbose = opts["verbose"]
        self.user2repo = {}
        self.repo2group = {}
        self.ta_assignments = {}
        self.course = conf["course"]
        self.assignment_name = conf["assignment_name"]
        self.starter_repo = conf["starter_repo"]
        self.github_org = conf["github_org"]
        self.archive_path = conf["archive_path"]
        self.submission_path = conf["submission_path"]
        self.ta_path = conf["ta_path"]
        self.feedback_branch = conf["feedback_branch"]
        if "do_not_accept_changes_after_due_date_timestamp" in conf:
            self.due_date = conf["do_not_accept_changes_after_due_date_timestamp"]
        self.anonymize_sub_path = conf["anonymize_sub_path"] if "anonymize_sub_path" in conf else True
        self.rsync_excludes = conf["rsync_excludes"]

        # populate mappings (user2repo, repo2group)
        for student in conf["repository_map"].keys():
            self.add_mapping(student, conf["repository_map"][student])

        # read TA list
        tas = conf["TAs"]
        tas.sort()  # sorting ensures that TA order is deterministic

        # generate TA map
        random.seed(Config.java_string_hashcode(conf["assignment_name"]))
        repos = self.repositories()
        random.shuffle(repos)
        self.ta_assignments = self.round_robin_map(tas, repos)

    def self_check(self):
        if spawn.find_executable("rsync") == None:
            print("ERROR: Cannot find rsync.", file=sys.stderr)
            sys.exit(1)

        if spawn.find_executable("git") == None:
            print("ERROR: Cannot find git.", file=sys.stderr)
            sys.exit(1)

    def round_robin_map(self, tas, repos):
        i = 0  # index into tas
        d = {} # map

        for r in repos:
            # assign TA to repository
            d[r] = tas[i]

            # advance TA index, wrapping if necessary
            i = i + 1
            if i >= len(tas):
                i = 0

        return d

    def list_of_users(self):
        return list(self.user2repo.keys())

    def add_mapping(self, user, repo):
        # pair user with repo
        self.user2repo[user] = repo

        # pair repo with group
        # first, check to see if repo already in dict
        if repo in self.repo2group:
            # yes, so get existing group and add user
            group = self.repo2group[repo]
            group = group.append(user)
        else:
            # no, so add repo and new group from user
            self.repo2group[repo] = [user]

    def lookupGroup(self, repo):
        return self.repo2group[repo]

    def lookupRepo(self, user):
        return self.user2repo[user]

    def pretty_print(self):
        print("Student -> repository map:")
        for user in self.user2repo.keys():
            print("  {} -> {}".format(user, self.user2repo[user]))

        print("TA -> repository map:")
        for repo in self.ta_assignments.keys():
            print("  {} -> {}".format(self.ta_assignments[repo],repo))

        print("archive path: {}".format(self.archive_path))
        print("submission path: {}".format(self.submission_path))
        print("ta path: {}".format(self.ta_path))
        print("course: {}".format(self.course))
        print("assignment name: {}".format(self.assignment_name))
        if hasattr(self, "do_not_accept_changes_after_due_date_timestamp"):
            print("due date: {}".format(datetime.datetime.fromtimestamp(int(self.due_date)).strftime('%Y-%m-%d %H:%M:%S')))
        print("feedback branch: {}".format(self.feedback_branch))

    def repositories(self):
        # sorting ensures that repository order is deterministic
        repos = list(self.repo2group.keys())
        return sorted(repos)

    def repo_ssh_path(self, repo):
        return "git@" + self.hostname + ":" + self.github_org + "/" + repo + ".git"

    def lookupTA(self, repo):
        return self.ta_assignments[repo]

    def pull_path(self, basepath, repo, use_user_name, anonymize):
        # if anonymize, then get the SHA1 hash of the repo name

        reponame = hashlib.sha1(repo.encode('utf-8')).hexdigest() if anonymize else repo

        if use_user_name:
            group = self.lookupGroup(repo)
            gname = Config.canonical_group_name(group)
            return os.path.join(basepath, gname, reponame)
        else:
            return os.path.join(basepath, reponame)

    # this method anonymizes the repository name
    def TA_target(self, ta_home, ta_dirname, repo):
        return os.path.join(ta_home, ta_dirname, self.lookupTA(repo),  hashlib.sha1(repo.encode('utf-8')).hexdigest())

    def pull_all(self, basepath, use_user_name, anonymize):
        # pull all repositories into archive and submission dirs
        for repo in self.repositories():
            rpath = self.pull_path(basepath, repo, use_user_name, anonymize)
            if not os.path.exists(rpath):
                # clone it
                print("Cloning {} to {}.".format(self.repo_ssh_path(repo), rpath))
                call(["git", "clone", self.repo_ssh_path(repo), rpath])
            else:
                # pull it
                print("Pulling {} to {}".format(self.repo_ssh_path(repo), rpath))
                Popen(["git", "pull"], cwd=rpath).wait() # note: blocking

            # if a due date was specified, roll back to due date
            if hasattr(self, "do_not_accept_changes_after_due_date_timestamp"):
                proc = Popen(
                      ["git",
                       "rev-list",
                       "-1",
                       "--before=\"" + str(self.due_date) + "\"", "master"],
                       stdout=PIPE,
                       stderr=PIPE,
                       cwd=rpath
                       )
                stdout, _ = proc.communicate() # note: blocking
                pathspec = stdout.rstrip()
                Popen(["git",
                       "checkout",
                       pathspec],
                       cwd=rpath).wait() # note: blocking

    def push_starter(self):
        print("starter repo is: {}", self.starter_repo)
        for repo in self.repositories():
            actual_repo = self.repo_ssh_path(repo)
            Popen(["git", "remote", "add", repo, actual_repo], cwd=self.starter_repo).wait()
            Popen(["git", "push", repo, "master"], cwd=self.starter_repo).wait()

    def copy_to_ta_folders(self, ta_home, ta_dirname, basepath):
        # keep track of repository -> TA map and print out the key
        # after doing all of the copying
        ta_map = []

        # cp all files except git stuff and other junk
        for repo in self.repositories():
            # compute target
            target = self.TA_target(ta_home, ta_dirname, repo)

            # save mapping
            ta_map.append((repo,target))

            if not os.path.exists(target):
                os.makedirs(target)
            # compute source; add slash so that rsync copies
            # _contents_ of folder into target
            source = self.pull_path(basepath, repo, False, self.anonymize_sub_path) + "/"

            # copy to ta folder
            if self.verbose:
                print("Copying from {} to {}".format(source, target))
            cmd = ["rsync",
                   "-vurlptoD" if self.verbose else "-urlptoD"]
            cmd.extend(["--exclude={}".format(e) for e in self.rsync_excludes])
            cmd.extend([source, target])
            call(cmd)
        # print mappings
        for (repo,target) in ta_map:
            print(repo + " -> " + target)

    def copy_from_ta_folders(self, ta_home, ta_dirname, basepath):
        # cp all files except git stuff
        for repo in self.repositories():
            # compute target
            target = self.pull_path(basepath, repo, False, self.anonymize_sub_path)
            # compute source; trailing slash is to force rsync to copy the CONTENTS
            # of source dir into the target dir, not to copy source dir into the target dir
            source = self.TA_target(ta_home, ta_dirname, repo) + "/"
            if not os.path.exists(target):
                # abort if target directory is missing!
                print("ERROR: Target submission directory {} is missing! Aborting.".format(target), file=sys.stderr)
                sys.exit(1)
                os.makedirs(target)
            # copy to ta folder
            if self.verbose:
                print("Copying from {} to {}".format(source, target))
            call(
                ["rsync",
                 "-vurlptoD" if self.verbose else "-urlptoD", #changed flags to maintain permissions
                 "--exclude=*/.git",
                 "--exclude=*/.gitignore",
                 "--exclude=*/*.class",
                 source,
                 target]
            )

    def branch_exists(self, rdir):
        # check to see if FEEDBACK_BRANCH branch exists
        proc = Popen(["git", "show-ref", "--verify", "--quiet", "refs/heads/" + self.feedback_branch],
                     stdout=PIPE,
                     stderr=PIPE,
                     cwd=rdir)
        proc.communicate() # note: blocking; don't care about output
        return proc.returncode == 0

    def commit_changes(self, basepath):
        for repo in self.repositories():
            # get submissions dir path for repo
            rdir = self.pull_path(basepath,  repo, False, self.anonymize_sub_path)
            if not self.branch_exists(rdir):
                # create branch
                if self.verbose:
                    print("Creating new branch {}".format(self.feedback_branch))
                Popen(["git", "checkout", "-b", self.feedback_branch], cwd=rdir).wait()
            else:
                Popen(["git", "checkout", self.feedback_branch], cwd=rdir).wait()
            # add any new files
            if self.verbose:
                print("Adding any new files in {}".format(rdir))
            Popen(["git", "add", "*"], cwd=rdir).wait() # note: blocking
            # commit
            if self.verbose:
                print("Committing feedback for " + rdir)
            Popen(["git", "commit", "-am", "TA feedback"], cwd=rdir).wait() # note: blocking

    # yeah, we brute force these...
    # fortunately, there aren't many to check
    def deanonymize_sha1_repo(self, anonrepo):
        for repo in self.repo2group.keys():
            utf8_repo = repo.encode('utf-8')
            repohash = hashlib.sha1(utf8_repo).hexdigest()
            if anonrepo == repohash:
                return repo
        print("ERROR: Could not deanonymize repository with SHA1 = " + anonrepo)
        sys.exit(1)

    def issue_pull_request(self, reponame, org):
        # extract basename
        bn = os.path.basename(reponame)

        # get real repository name if hashed
        repo = self.deanonymize_sha1_repo(bn) if self.anonymize_sub_path else bn

        # get submissions dir path for repo
        rdir = self.pull_path(self.submission_path, reponame, False, False)
        
        # obtain handle to remote repository
        grepo = org.get_repo(repo)

        # ensure that the master branch exists on remote
        remote_branches = []
        for rb in grepo.get_branches():
            remote_branches.append(rb.name)

        if "master" not in remote_branches:
            print("ABORT: master branch does not exist in remote repository.")
            return errno.ENOENT

        if self.feedback_branch in remote_branches:
            print("ABORT: {} branch already exists in remote repository.".format(self.feedback_branch))
            return errno.EEXIST


        if self.verbose:
            print("Pushing branch {} to origin.".format(self.feedback_branch))

        #### Lida: needed to edit since reponame contains the relative path, not just the name ####
        #### Dan/Bill: not sure why this is necessary... hopefully we trigger it again and figure out why...
        #Popen(["git", "push", "origin", self.feedback_branch], cwd=reponame).wait()
        Popen(["git", "push", "origin", self.feedback_branch], cwd=rdir).wait()
        
        # create pull request
        if self.verbose:
            print("Issuing pull request from branch '{}' to branch 'master' in {}.".format(self.feedback_branch, repo))

        # push commits upstream

        # we get the repo name from github so that you can run
        # this command from other locations
        grepo = org.get_repo(os.path.basename(repo))
        grepo.create_pull(
            title = "Feedback",
            base = "master",
            head = self.feedback_branch,
            body = "Feedback on " + self.assignment_name + " from " + self.course + " teaching staff."
        )
        return 0
