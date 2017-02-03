#!/usr/bin/env python

import jinja2
import json
import logging
import os
import re
import shutil
import sqlite3
import sys

from rebase_report import disk
from rebase_report import git
from rebase_report import hooks
from rebase_report.hooks import before
from rebase_report.hooks import after

LOG = logging.getLogger('git-rebase')
logging.basicConfig(level=logging.DEBUG)


def get_changelist():
    path = os.path.join(git.dot_git_dir(), 'rebase.todo')
    changes = []
    with open(path, 'r') as f:
        for line in f:
            if not line.strip():
                return changes
            parts = line.split(' ', 2)
            msg = git.get_commit_message(parts[1])
            tickets = re.findall('SOLAR-[\d]+', msg)
            tickets += re.findall('GALACTIC-[\d]+', msg)
            changes.append({
                'action': parts[0],
                'commit': parts[1],
                'title': parts[2],
                'tickets': tickets
            })

def report():
    data = {}

    with sqlite3.connect(git.rebase_db()) as c:
        c.text_factory = str
        c.row_factory = sqlite3.Row
        cursor = c.cursor()
        cursor.execute('select * from conflicts where commit_sha is not null')

        # parse each conflict
        for conflict in cursor.fetchall():
            LOG.debug('Processing conflict %s' % conflict['id'])

            cursor.execute('select * from tickets where conflict_id=?', (conflict['id'],))
            tickets = cursor.fetchall()
            tickets = ['-'.join([t['team'], str(t['ticket'])]) for t in tickets]

            cursor.execute('select * from files where conflict_id=?', (conflict['id'],))
            files = [dict(f) for f in cursor.fetchall()]

            cursor.execute('select * from messages where conflict_id=?', (conflict['id'],))
            messages = {msg['sha']: msg['text'] for msg in cursor.fetchall()}

            data[conflict['commit_sha']] = {
                'tickets': tickets,
                'files': files,
                'messages': messages,
                'shas': {
                    'onto': conflict['onto_sha'],
                    'stopped': conflict['stopped_sha'],
                }
            }

        with open('output.html', 'w') as output_file:
            template = disk.get_jinja_template()
            output_file.write(template.render(
                changelist=get_changelist(),
                data=data,
                json_data=json.dumps(data),
                basename=os.path.basename
            ))

@before('rebase')
def initialize():
    """Create a directory for saving rebase info.
    """
    if not (git.is_rebasing()):
        LOG.debug('Initializing database..')
        try:
            with sqlite3.connect(git.rebase_db()) as c:
                c.text_factory = str
                cursor = c.cursor()
                cursor.executescript(disk.get_schema())
        except Exception as e:
            LOG.error(str(e))

@after('rebase', ['-i', '--interactive'])
def saveTodo():
    if (git.is_rebasing()):
        LOG.debug('Saving copy of todo..')
        path = os.path.join(git.dot_git_dir(), 'rebase.todo')
        shutil.copy(git.rebase_todo(), path)

def get_conflict_files():
    with sqlite3.connect(git.rebase_db()) as c:
        c.text_factory = str
        cursor = c.cursor()
        cursor.execute('select path from files where conflict_id=?', (conflict_id(),))
        files = [line[0] for line in cursor.fetchall()]
        return files


@after('rebase')
def saveAnyConflicts():
    if (git.is_rebasing()):

        parent = git.current_sha()
        stopped = git.stopped_sha()
        onto = git.onto_sha()

        with sqlite3.connect(git.rebase_db()) as c:
            c.text_factory = str
            cursor = c.cursor()
            cursor.execute('insert into conflicts values(null, ?, ?, ?, ?)', (None, parent, stopped, onto,))
            conflict_id = cursor.lastrowid

            LOG.debug('Stopped SHA is %s' % git.stopped_sha())
            LOG.debug('Onto SHA is %s ' % git.onto_sha())

            # save ticket numbers from stop commit
            stopped_msg = git.get_commit_message(git.stopped_sha())
            c.execute('insert into messages values(null, ?, ?, ?)',
                          (conflict_id, stopped_msg, git.stopped_sha()))
            tickets = re.findall('SOLAR-[\d]+', stopped_msg)
            tickets += re.findall('GALACTIC-[\d]+', stopped_msg)

            # save ticket numbers from onto commit
            onto_msg = git.get_commit_message(git.onto_sha())
            c.execute('insert into messages values(null, ?, ?, ?)',
                          (conflict_id, onto_msg, git.onto_sha()))
            tickets += re.findall('SOLAR-[\d]+', onto_msg)
            tickets += re.findall('GALACTIC-[\d]+', onto_msg)

            for ticket in tickets:
                team, number = ticket.split('-')
                c.execute('insert into tickets values(null, ?, ?, ?)', (conflict_id, team, number,))

            # save each conflict
            for conflict in git.list_conflicts():

                combined = None

                # save stopped file
                stopped_file = git.get_file_for_commit(conflict, stopped)

                # save onto file
                onto_file = git.get_file_for_commit(conflict, onto)

                # copy combined
                if os.path.exists(conflict):
                    combined = disk.grab_file(conflict)

                c.execute('insert into files values(null, ?, ?, ?, ?, ?, ?, ?)',
                                (conflict_id, conflict, None, combined, stopped_file, onto_file, None))

@after('rebase', ['--continue'])
def assignCommitForConflict():
    cid = conflict_id() - 1

    with sqlite3.connect(git.rebase_db()) as c:
        c.text_factory = str
        cursor = c.cursor()
        cursor.execute('select parent_sha from conflicts where id=?', (cid,))

        parent_sha = cursor.fetchone()[0]
        sha = git.get_next_sha(parent_sha)
        msg = git.get_commit_message(sha)

        c.execute('update conflicts set commit_sha=? where id=?', (sha, cid))
        c.execute('insert into messages values(null, ?, ?, ?)', (cid, msg, sha))

def conflict_id():
    with sqlite3.connect(git.rebase_db()) as c:
        c.text_factory = str
        cursor = c.cursor()
        cursor.execute('select id from conflicts where stopped_sha=? and onto_sha=?', (git.stopped_sha(), git.onto_sha()))
        conflict_id = cursor.fetchone()[0]
        return conflict_id

@before('rebase', ['--continue'])
def clone_before_continue():
    """Makes copies of files."""
    data = {}
    for line in git.diff_status():
        if len(line) == 2:
            data[line[1]] = line[0]

    with sqlite3.connect(git.rebase_db()) as c:
        c.text_factory = str
        paths = get_conflict_files()
        for path in paths:
            f = None
            status = data.get(path, 'D')
            if status != 'D':
                f = disk.grab_file(path)
            c.execute('update files set resolved=?, status=? where conflict_id=? and path=?',
                          (f, status, conflict_id(), path,))

@after('status')
def stuff():
    if (git.is_rebasing()):
        LOG.debug('Current commit is %s' % git.current_sha())
        LOG.debug('Stopped sha is %s' % git.stopped_sha())
        LOG.debug('Onto sha is %s' % git.onto_sha())

@before('rebase', ['--abort'])
def clean():
    try:
        os.remove(git.rebase_db())
        path = os.path.join(git.dot_git_dir(), 'rebase.todo')
        os.remove(path)
    except Exception as e:
        LOG.error(str(e))

# main
def main():
    args = sys.argv[1:]
    if len(args) == 0:
        print git.call(args)
        return
    command = args[0]
    if (command == 'report'):
        report()
        return
    if (command in hooks._before):
        hooks._before[command].run(args[1:])
    output = git.call(args)
    if (command in hooks._after):
        hooks._after[command].run(args[1:])
