import os
import subprocess

GIT = subprocess.check_output(['whereis', 'git'], env={}).strip()

def check_output(args):
    try:
        return subprocess.check_output([GIT] + args, stderr=subprocess.STDOUT, universal_newlines=True).strip()
    except subprocess.CalledProcessError as e:
        return e.output

def call(args):
    try:
        return subprocess.call([GIT] + args)
    except subprocess.CalledProcessError as e:
        return e.output

def current_sha():
    return check_output(['rev-parse', 'HEAD'])

def top_level():
    return check_output('rev-parse --show-toplevel'.split(' '))

def dot_git_dir():
    return os.path.join(top_level(), '.git')

def rebase_dir():
    return os.path.join(dot_git_dir(), 'rebase-merge')

def rebase_db():
    return os.path.join(dot_git_dir(), 'rebase.db')

def is_rebasing():
    return os.path.exists(rebase_dir())

def rebase_todo():
    return os.path.join(rebase_dir(), 'git-rebase-todo.backup')

def is_git_repo():
    return check_output(['status'])[0]

def stopped_sha():
    path = os.path.join(rebase_dir(), 'stopped-sha')
    with open(path, 'r') as f:
        return f.readline().strip()

def onto_sha():
    path = os.path.join(rebase_dir(), 'onto')
    with open(path, 'r') as f:
        return f.readline().strip()

def get_commit_message(commit):
    return check_output(['log', '-n', '1', commit])

def diff_status():
    output = check_output(['diff', '--name-status', '--cached'])
    return [line.split('\t') for line in output.split('\n')]

def get_file_for_commit(path, commit):
    return check_output(['show', commit+':'+path])

def list_conflicts():
    return check_output(['diff', '--name-only', '--diff-filter=U']).split('\n')

def get_next_sha(commit):
    return check_output(['log', commit+'..HEAD', '--oneline', '--reverse']).split('\n')[0].split(' ')[0]

