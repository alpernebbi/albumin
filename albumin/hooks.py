# Albumin Git Hooks
# Copyright (C) 2016 Alper Nebi Yasak
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import pytz

from albumin.repo import AlbuminRepo
from albumin.imdate import Report


def pre_commit_hook(args):
    """
    Albumin as a pre-commit hook.
    Usage: pre-commit
    """
    repo = current_repo()
    new_files = repo.new_files()

    if not repo.in_master_branch():
        print("Not in master branch.")
        return 4

    try:
        timezone = repo.timezone
    except pytz.exceptions.UnknownTimeZoneError as err:
        print("Invalid time zone: {}".format(err))
        return 1

    if new_files and not timezone:
        print("Please set albumin.timezone:")
        print("    $ git -c albumin.timezone=UTC commit ...")
        return 2

    report = repo.imdate_diff(
        {repo.abs_path(f): k for f, k in new_files.items()}
    )

    if report.remaining:
        print('Some files in report have no information:')
        print(report)
        return 3

    report = Report(new_files, report.updates, set())

    updates = report.updates
    file_data = {
        key: updates[key][0]
        for file, key in new_files.items()
        if key in updates
    }

    repo.arrange_by_imdates(imdates=file_data)
    repo.annex.pre_commit()

    msg_path = os.path.join(repo.path, 'albumin.msg')
    with open(msg_path, 'w') as msg_file:
        print(*report.short(), sep='\n', file=msg_file)


def prepare_commit_msg_hook(args):
    """
    Albumin as a pre-commit git hook.
    Usage: prepare-commit-msg <editmsg> [[<commit_type>] <commit_sha>]
    """
    repo = current_repo()
    msg_path = os.path.join(repo.path, 'albumin.msg')

    try:
        with open(msg_path, 'r') as msg_file:
            report = [line.strip() for line in msg_file]
    except FileNotFoundError:
        report = []

    if args['<commit_type>'] == 'message':
        with open(args['<editmsg>'], 'r') as editmsg:
            message = [line.strip() for line in editmsg]

    elif args['<commit_type>'] == 'commit':
        if args['<commit_sha>'] == 'HEAD':
            message = repo.head.get_object().message.splitlines()

    elif not args['<commit_type>']:
        message = []
        tags = {}

    try:
        head, tags, report_ = parse_commit_msg(message)
        title = "\n".join(head)
        report = list(report_.short()) + report
    except:
        title = "\n".join(message)
        tags = {}

    def new_message():
        yield title
        yield ''
        yield '[tags]'
        yield from ('{}: {}'.format(t, v) for t, v in tags.items())
        yield ''
        yield '[report]'
        yield from report

    with open(args['<editmsg>'], 'w') as editmsg:
        print(*new_message(), sep='\n', file=editmsg)


def commit_msg_hook(args):
    """
    Albumin as a pre-commit git hook.
    Usage: commit-msg <editmsg>
    """
    repo = current_repo()

    with open(args['<editmsg>'], 'r') as editmsg:
        msg = (line.strip() for line in editmsg)
        msg = [line for line in msg if not line.startswith('#')]

    if not msg:
        print('Empty commit message.')
        return 6

    head, tags, report = parse_commit_msg(msg)

    if report.remaining:
        print('Report shouldn\'t have no-info elements, but does:')
        print(*report.remaining, sep='\n')
        return 1

    new_files = {
        os.path.basename(f): k for f, k in repo.new_files().items()
    }

    for file, key in report.files.items():
        name = os.path.basename(file)

        if file in report.redundants:
            imdate = repo.annex[key].imdate
        elif file in report.additions:
            _, imdate = report.additions[file]
        elif file in report.overwrites:
            _, imdate, _ = report.overwrites[file][1]
        else:
            print('Check file in report:')
            print(file, key, sep='\n')
            return 2

        utc = imdate.datetime.astimezone(pytz.utc)
        ext = os.path.splitext(key)[1]
        dt_name = '{:%Y%m%dT%H%M%SZ}{{:02}}{}'.format(utc, ext)

        for i in range(100):
            new_name = dt_name.format(i)
            if new_files.get(new_name) == key \
                    or repo.annex.lookupkey(new_name) == key:
                break
        else:
            print('Can\'t find {} with key:'.format(dt_name))
            print('    {}'.format(key))
            return 3

    for tag, value in tags.items():
        if tag in repo.annex.internal_tags:
            print('Invalid tag: {}'.format(tag))
            return 4

        if tag.endswith('lastchanged'):
            print('Tags can\'t end with lastchanged: {}'.format(tag))
            return 5

    def new_message():
        yield from head
        if tags:
            yield ''
            yield '[tags]'
            yield from ('{}: {}'.format(t, v) for t, v in tags.items())
        if report:
            yield ''
            yield '[report]'
            yield from report.short()

    with open(args['<editmsg>'], 'w') as editmsg:
        print(*new_message(), sep='\n', file=editmsg)


def post_commit_hook(args):
    """
    Albumin as a post-commit git hook.
    Usage: post-commit
    """
    repo = current_repo()
    msg_head, tags, report = parse_commit_msg()

    for _, (key, new_imdate) in report.additions.items():
        repo.annex[key].imdate = new_imdate
    for _, (key, new_imdate, _) in report.overwrites.items():
        repo.annex[key].imdate = new_imdate
    for _, key in report.files.items():
        repo.annex[key].update(tags)

    msg_path = os.path.join(repo.path, 'albumin.msg')
    if os.path.exists(msg_path):
        os.remove(msg_path)


def parse_commit_msg(msg=None):
    if msg is None:
        repo = current_repo()
        msg = repo.head.get_object().message.splitlines()
    msg = [m for m in msg if not m.startswith('#')]

    msg_head = []
    for line in msg:
        if line.startswith('[') and line.endswith(']'):
            break
        msg_head.append(line)

    if not msg_head[-1]:
        msg_head.pop()

    def section(header):
        try:
            idx = msg.index(header) + 1
        except ValueError:
            return []

        try:
            len_ = msg[idx:].index('')
        except ValueError:
            return msg[idx:]
        else:
            return msg[idx:idx+len_]

    tags = dict(x.split(': ') for x in section('[tags]'))
    report = Report.parse(section('[report]'))

    return msg_head, tags, report


def current_repo():
    return AlbuminRepo(os.getcwd(), create=False)


git_hooks = {
    'pre-commit': pre_commit_hook,
    'prepare-commit-msg': prepare_commit_msg_hook,
    'commit-msg': commit_msg_hook,
    'post-commit': post_commit_hook,
}
