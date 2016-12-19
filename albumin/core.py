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

    title = 'Batch: {}'.format(batch)
    tags_ = '\n'.join('{}: {}'.format(t, v) for t, v in tags.items())
    report_ = '\n'.join(report(imported_files, updates, remaining))
    commit_msg = '\n\n'.join((title, tags_, report_))

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

    else:
        files = {f: f for f in files}
        additions, remaining = analyze_date(*files)

        if timezone:
            for imdate in additions.values():
                imdate.timezone = timezone

        updates = {f: (v, None) for f, v in additions.items()}

    report_ = report(files, updates, remaining)
    report_ = merge_report(report_)
    if not repo:
        report_ = filter_report(report_, '[F+]')
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
        yield '[F?] {key}: '.format(key=key)
        yield '[..]   {file}'.format(file=file)

    for file, (key, _) in additions.items():
        yield '[F+] {key}: '.format(key=key)
        yield '[..]   {file}'.format(file=file)

    for file, (key, _, _) in overwrites.items():
        yield '[F!] {key}: '.format(key=key)
        yield '[..]   {file}'.format(file=file)

    for file, key in redundants.items():
        yield '[F=] {key}: '.format(key=key)
        yield '[..]   {file}'.format(file=file)

    for _, (key, new) in additions.items():
        yield '[T+] {key}: '.format(key=key)
        yield '[..]   {new}'.format(new=new)

    for _, (key, new, old) in overwrites.items():
        yield '[T!] {key}: '.format(key=key)
        yield '[..]   {new} <- {old}'.format(new=new, old=old)


def filter_report(report, *remove):
    filter_dots = False

    for line in report:
        prefix = line[:4]

        if prefix == '[..]' and filter_dots:
            continue

        filter_dots = prefix in remove
        if prefix in remove:
            continue

        yield line


def merge_report(report):
    merged = None

    for line in (*report, '!EOF'):
        prefix = line[:4]

        if not merged:
            merged = line
            continue

        if prefix == '[..]':
            merged += line[7:] + ', '
            continue

        if merged.endswith(', '):
            yield merged[:-2]
        else:
            yield merged
        merged = line


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

