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

from datetime import datetime

from albumin.utils import files_in
from albumin.imdate import analyze_date
from albumin.report import Report


def import_(repo, path, **tags):
    batch, files, updates, remaining = repo.import_(path, **tags)
    timestamp = datetime.strptime(batch, '%Y%m%dT%H%M%SZ')
    report = Report(files, updates, remaining)

    title = 'Batch: {}'.format(batch)
    tags_ = '\n'.join('{}: {}'.format(t, v) for t, v in tags.items())
    commit_report = '\n'.join(report.short())
    commit_msg = '\n\n'.join((title, tags_, commit_report))
    repo.commit(commit_msg, timestamp=timestamp)

    print(title, tags_, report, sep='\n\n')


def repo_analyze(repo, path=None):
    files, updates, remaining = repo.analyze(path=path)
    report = Report(files, updates, remaining)
    print(report)


def imdate_analyze(path, timezone=None):
    files = list(files_in(path))
    additions, remaining = analyze_date(*files, timezone=timezone)
    report = Report(files, additions, remaining)
    print(report, sep='\n')
