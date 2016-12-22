# Albumin Core
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
from datetime import datetime

from albumin.utils import files_in
from albumin.imdate import analyze_date
from albumin.hooks import git_hooks


def init(repo, exec_path):
    for hook in git_hooks:
        path = os.path.join(repo.path, 'hooks', hook)

        if os.path.exists(path) and hook != 'pre-commit':
            print('Repo already has hooks:')
            raise RuntimeError(hook)

        elif hook == 'pre-commit':
            with open(path) as file:
                content = file.readlines()

            if content != [
                '#!/bin/sh\n',
                '# automatically configured by git-annex\n',
                'git annex pre-commit .\n',
            ]:
                print('Unexcpected pre-commit hook:')
                raise RuntimeError(content)
            else:
                os.remove(path)

    for hook in git_hooks:
        path = os.path.join(repo.path, 'hooks', hook)
        os.symlink(exec_path, path)


def import_(repo, path, **tags):
    batch, report = repo.import_(path, **tags)
    timestamp = datetime.strptime(batch, '%Y%m%dT%H%M%SZ')

    def commit_msg():
        yield 'Batch: {}'.format(batch)
        yield ''
        yield '[tags]'
        yield 'batch: {}'.format(batch)
        yield from ('{}: {}'.format(t, v) for t, v in tags.items())
        yield ''
        yield '[report]'
        yield from report.short()

    commit_msg = '\n'.join(commit_msg())
    repo.commit(commit_msg, timestamp=timestamp)
    print(commit_msg)


def repo_analyze(repo, path=None):
    report = repo.analyze(path=path)
    print(report)


def imdate_analyze(path, timezone=None):
    report = analyze_date(*files_in(path), timezone=timezone)
    print(report)
