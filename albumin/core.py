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
import pytz
import pygit2
from datetime import datetime
from collections import OrderedDict

from albumin.utils import files_in
from albumin.imdate import analyze_date


def import_(repo, import_path, timezone=None, tags=None):
    if not tags:
        tags = {}

    imported_files = repo.annex.import_(import_path)
    repo.annex.clear_metadata_cache()

    updates, remaining = repo.imdate_diff(
        {repo.abs_path(f): k for f, k in imported_files.items()},
        timezone=timezone
    )
    if remaining:
        raise NotImplementedError(remaining)
    if not updates:
        print('All files and info already in repo.')
        return

    for key, (new_imdate, _) in updates.items():
        repo.annex[key].imdate = new_imdate

    batch = repo.arrange_by_imdates()
    timestamp = datetime.strptime(batch, '%Y%m%dT%H%M%SZ')

    commit_author = pygit2.Signature(
        repo.default_signature.name,
        repo.default_signature.email,
        int(timestamp.timestamp())
    )

    commit_msg = "\n".join((
        'Batch: {}'.format(batch),
        '',
        'Imported from:',
        '{}'.format(import_path),
        '',
        'Tags: ',
        'batch: {}'.format(batch),
        'timezone: {}'.format(timezone),
        *('{}: {}'.format(tag, value) for tag, value in tags.items()),
        '',
        'Report:',
        *report(imported_files, updates, remaining)
    ))

    commit = repo.create_commit(
        'HEAD',
        commit_author,
        commit_author,
        commit_msg,
        repo.index.write_tree(),
        [repo.head.get_object().hex]
    )


def analyze(analyze_path, repo=None, timezone=None):
    files = list(files_in(analyze_path))

    if repo:
        files = {f: repo.annex.calckey(f) for f in files}
        updates, remaining = repo.imdate_diff(files, timezone=timezone)
        report_ = report(files, updates, remaining)

    else:
        files = {f: f for f in files}
        additions, remaining = analyze_date(*files)

        if timezone:
            for imdate in additions.values():
                imdate.timezone = timezone

        updates = {f: (v, None) for f, v in additions.items()}
        report_ = report(files, updates, remaining)
        report_ = filter(lambda s: not s.startswith('[F+]'), report_)

    report_ = format_report(report_)
    print(*report_, sep='\n')


def report(files, updates, remaining):
    overwrites, additions, redundants = {}, {}, {}

    for file, key in files.items():
        new, old = updates.get(key, (None, None))
        if new and old:
            overwrites[file] = (key, new, old)
        elif new:
            additions[file] = (key, new)
        elif file not in remaining:
            redundants[file] = key

    def sort_key(t):
        path, _ = t
        return os.path.split(path)

    def sorted_dict(d):
        return OrderedDict(sorted(d.items(), key=sort_key))

    overwrites = sorted_dict(overwrites)
    additions = sorted_dict(additions)
    redundants = sorted_dict(redundants)
    remaining = sorted_dict({f: files[f] for f in remaining})

    for file, key in remaining.items():
        yield '[F?] {key}: {file}'.format(file=file, key=key)

    for file, (key, _) in additions.items():
        yield '[F+] {key}: {file}'.format(file=file, key=key)

    for file, (key, _, _) in overwrites.items():
        yield '[F!] {key}: {file}'.format(file=file, key=key)

    for file, key in redundants.items():
        yield '[F=] {key}: {file}'.format(file=file, key=key)

    for _, (key, new) in additions.items():
        yield '[T+] {key}: {new}'.format(key=key, new=new)

    for _, (key, new, old) in overwrites.items():
        yield '[T!] {key}: {new}'.format(key=key, new=new)
        yield '[..] {} vs: {old}'.format(' ' * (len(key)-3), old=old)


def format_report(report):
    sections = {
        '[F?]': 'No Information:',
        '[F+]': 'New Files:',
        '[F!]': 'Updated Files:',
        '[F=]': 'Redundant Files:',
        '[T+]': 'Datetime Additions:',
        '[T!]': 'Datetime Overwrites:',
    }
    current = None

    for line in report:
        prefix = line[:4]
        section = sections.get(prefix, current)

        if current != section:
            if current:
                yield ''
            current = section
            yield current

        yield '  ' + line[5:]

