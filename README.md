# Github-based grading management scripts

## What

This project is a collection of grading scripts that facilitate the large-scale management of GitHub repositories for students to use to submit homework assignments.  With these tools, you may:

* Automatically create GitHub repositories and pre-populate them with starter code.
* Automatically clone, archive, and distribute repositories to teaching staff for distributed grading tasks.
* Automatically commit TA and instructor feedback, which is then relayed back to students in the form of GitHub pull requests.

No tedious interaction with the GitHub website is necessary as all configuration and management can be performed using the command line.

## Installation Using Python3 Virtual Environment

In order to run these scripts on a system where you do not have the capability (or desire) to install system-wide packages (e.g. `PyGithub`), you can use a [virtual environment](https://docs.python.org/3/tutorial/venv.html)
to isolate the Python libraries necessary to use the GitHub software.

  * create a virtual environment for your repo
  ```
  python3 -m venv venv
  ```
  or
  ```
  make setup
  ```
  * activate your virtual environment
  ```
  source venv/bin/activate
  ```
  You will see the addition of `(venv)` in front of your terminal prompt. This
  indicates that you are inside your virtual environment. You can install packages using `pip` and run programs using `python` and everything will be self contained within your virtual environment.

  * install necessary libraries
  ```
  pip install PyGithub
  ```

At this point, you can run any of the python scripts you would like.

  * when you are finished, you can "deactivate" your virtual environment
  ```
  deactivate
  ```
In the future, you will _not_ need to recreate the virtual environment. However,
you will need to _activate_ your virtual environment every time.
  ```
  source venv/bin/activate
  ```

## Configuration

You must write a configuration file for _each homework assignment_ you wish to manage using these scripts.

Configuration is done using a `config.json` file.  You may find the included `config.json.template` file to be a helpful template.

The complete set of configuration options are as follows:

|option|type|example|description|
|------|----|-------|-----------|
|`"hostname"`|`string`|`"github-williams"`|The name of your SSH `config` host to use for script interaction.  This allows you to use a different GitHub identity for managing course scripts because, presently, PyGithub does not support two-factor authentication.|
|`"course"`|`string`|`"cs334"`|The name of the course.|
|`"assignment_name"`|`string`|`"hw1"`|The name of the assignment.|
|`"do_not_accept_changes_after_due_date_timestamp"`|`int` (optional)|`1520467199`|A UNIX timestamp representing the due date in the local timezone.|
|`"anonymize_sub_path"`|`bool` (optional)|`false`|Controls whether the contents of the `submissions` folder, which is viewable only by faculty (not TAs), is anonymized.  If omitted, the default value is `true`.|
|`"archive_path"`|`string`|`"/path/to/archive"`|Path to folder intended as deanonymized repository of student submissions for Academic Honor Code cases.|
|`"submission_path"`|`string`|`"/path/to/submissions"`|Path to faculty-only staging area for squashing and modifying TA feedback before issuing pull requests.|
|`"ta_path"`|`string`|`"/path/to/TAs"`|Path to TA staging area where anonymized student submissions are copied.|
|`"feedback_branch"`|`string`|`"assignment-feedback"`|Branch to commit TA/instructor feedback on. Pull requests are issued from this branch.|
|`"starter_repo"`|`string`|`"/home/example/starter-repo"`|Path to starter repo.  Starter code is distributed by setting each student repository as a "remote" for the starter repository and then `push`ing.  Student repositories _must_ be empty (i.e., no `master` branch) otherwise `push` will fail.|
|`"github_org"`|`string`|`"williams-cs"`|Name of the GitHub organization to use.|
|`"TAs"`|`string[]`|`[ "ta1", "ta2", "ta3" ]`|TA names to use as folder names.  These need not be tied to actual account names.  Names are appended to the `ta_path` and files are copied to the resulting path.|
|`"repository_map"`|`dict<string,string>`|`{"dbarowy": "cs999_hw1_dbarowy", "wjannen": "cs999_hw1_wjannen"}`|Dictionary mapping student GitHub usernames to repositories in the `github_org` organization. Should not be created manually; instead paste in output after running `populate-github` command.|

## Online Help

Note that, when run with no arguments, all scripts print a help message:

```
$ populate-github.py 
Usage: populate-github.py [flags] <github username> <github password> <course name> <assignment name> <student name file>
        where flags are:
        -d      dry run; do not create repositories but print out student and repo names.
```

## Use

Use scripts as a part of the following workflow:

### Step 1. Generate Team Names

1. Create a file with student teams, one team's github username(s) per line. For individual assignments, this would mean one username per line. For partner assignments, this would mean a `.csv` file where each line is a comma separated list of student github usernames.

### Step 2. Generate Config File

1. Run `generate-config.py <student name file> <base config template>` to create a student config file. You should copy `config.json.template` and edit the necessary fields. The python script will fill in the repository information using the information from the student file name (the first argument, created in step 1 above)

### Step 3. Populate Repositories

1. (optional) If starter code is to be distributed, create a git starter code repository.
1. Create a file containing a list of student/group names.  Each line in the file should contain a comma-separated list of students, like `student1,student2,student3` which will create a single repository for all students listed.  Groups need not be the same size.  If groups are not needed, simply list a single student per line. _Each student name should be the name of that student's GitHub account._ 
1. Run the `populate_github.py` command to create repositories for students.  This command will print out a JSON dictionary that you must use for your `repository_map` in your JSON config file. After creation, students will receive an email invitation to contribute to the repository.
1. Create a config file using the `repository_map` from the previous step.  You should probably use the template `config.json.template` distributed with this project.
1. If you are distributing starter code, run `push-starter.py`, supplying your JSON config on the command line.  Your config file should specify the location of the starter code repository. This program actually modifies the `.git/config` entry in that file with additional "remotes". It then pushes the starter files to those remotes using `git push`

Students will now have repositories (optionally pre-populated with starter code) to use for their assignments.

### Step 4. Fetch Student Work

This step locally clones student work to the `archive_path`, `submission_path`, and `ta_path` configured in the JSON config file.  Ideally, those paths are located in a shared directory (e.g., an NFS export) so that TAs and other teaching staff can access the files.  We strongly suggest that you set filesystem permissions so that the `archive_path` and `submission_path` are readable/writable only by faculty.  The `ta_path` should readable/writable by TAs.  None of the paths should be readable/writeable by students in the course.  **NOTE: Allowing students to read/write to any these directories jeopardizes the integrity of the grading process!**

1. At the due date, run `get-submissions.py` to download student work.  This step may be automated using `cron` if desired.  Note that if a `do_not_accept_changes_after_due_date_timestamp` is set, the last commit before the due date is fetched, otherwise the latest commit is fetched.  Work will be placed in three directories:
    1. `archive_path`: This is a read-only collection of student submissions, archived for honor-code cases. Git information is preserved.
    1. `submission_path`: This is a read-write collection student submissions.  Pull requests will be generated from here.  Git information is preserved.
    1. `ta_path`: This folder, which is organized into TA-specific subfolders, holds student submissions scrubbed of identifying information and git histories.
  
  After running this command, you should notify your TAs that submissions are available for them to review.  TAs then edit files in their folders, adding feedback as necessary.  We typically instruct TAs to create a `grade.txt` file for grading feedback and comments, but TAs may also modify files as needed (e.g., to insert comments inline).  Many TAs find it helpful if you generate a `grade.txt` template for them to use, which also ensures some uniformity in grading.
  
  `get-submissions.py` prints out a TA-repository name map that you may wish to store for use in the next step, as the assignment of TAs to repositories is (pseudo)random (and deterministic, using a hash of the `assingment_name` as a random seed).

### Step 5. Collect TA Feedback

1. When TAs are done grading (or on a given date), run `commit-feedback.py` to copy feedback from the `ta_path` to the `submission_path`.  TA feedback will be committed to the `feedback_branch` specified in the config file.

Course instructors should review TA feedback for each repository in the `submission_path` folder, committing additional feedback as necessary and squashing merges to hide TA mistakes (if necessary). When done, use the command `git commit --amend` to overwrite the commit created by `commit-feedback.py` with your authoritative commit. This hides the TA's identity and makes you the sole author of the feedback commit.

Note that if the `anonymize_sub_path` is either omitted or set to true, repository names in this folder will be anonymized using SHA1 hashes.  However, `git` histories and other identity-preseving files (like `README.md` and `collaborators.txt`) will be preserved.  In order to preserve anonymity during grading, instructors should avoid reading these files until after grading is complete.

### Step 6: Issue Pull Request to Student

1. When instructor-reviewed feedback is ready, run `issue-pull-requests.py` to push the `TA-feedback` branch upstream and create a pull request.  Note that, unlike the other commands, this command needs to be issued once for every repository.

Note that, if `anonymize_sub_path` is `true`, which it is by default, you must use the SHA-1 hash name of the repository as the repository name.  Otherwise, you should use the real repository name.  Either way, the easiest way to remember which to use is to simply copy the name of the folder present in the `submission_path` directory.  You may either use an absolute path (e.g., `/home/courses/csXXX/submissions/513a1830031f4a76389d6d47a9a4ec7f9e146438`) or just the basename (e.g., `513a1830031f4a76389d6d47a9a4ec7f9e146438`) for the repository.

Students should be instructed to acknowledge the receipt of their feedback by accepting the pull request.  They may also engage the instructor for additional feedback by using the comment feature that comes with GitHub's pull request tool.
