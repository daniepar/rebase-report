# rebase-report
Generates a HTML report that shows what changes were made by the person doing the rebase.

## Installation
_Note: Because this overrides the Git command, it is highly recommended to install this in a virtual environment._
```bash
virtualenv venv
. venv/bin/activate
pip install git+https://github.com/daniepar/rebase-report.git
```

## Usage
``rebase-report`` must be activated before starting a rebase; this allows it to collect information as you are doing the rebase.

1. Activate the virtual environment that has ``rebase-report`` installed:

  ```bash
  $ . venv/bin/activate
  ```
1. Begin the rebase:

  ```bash
  (venv) $ cd my_repo
  (venv) $ git rebase -i some_branch
  ```
1. After the rebase completes, generate a report:

  ```bash
  (venv) $ git report
  ```
1. Once you're happy with the report, deactivate the virtual environment:

  ```bash
  (venv) $ deactivate
  ```
