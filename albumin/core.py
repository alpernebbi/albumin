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
from collections import OrderedDict

from albumin.utils import files_in
from albumin.imdate import analyze_date


def import_(repo, path, **tags):
    batch, files, updates, remaining = repo.import_(path, **tags)
    timestamp = datetime.strptime(batch, '%Y%m%dT%H%M%SZ')
    short_report = list(report(files, updates, remaining))

    title = 'Batch: {}'.format(batch)
    tags_ = '\n'.join('{}: {}'.format(t, v) for t, v in tags.items())
    commit_report = '\n'.join(short_report)

    commit_msg = '\n\n'.join((title, tags_, commit_report))
    repo.commit(commit_msg, timestamp=timestamp)

    long_report = format_report(merge_report(short_report))
    print(title, tags_, sep='\n\n', end='\n\n')
    print(*long_report, sep='\n')


def repo_analyze(repo, path=None):
    files, updates, remaining = repo.analyze(path=path)
    short_report = report(files, updates, remaining)
    long_report = format_report(merge_report(short_report))
    print(*long_report, sep='\n')


def imdate_analyze(path, timezone=None):
    files = {f: f for f in files_in(path)}
    additions, remaining = analyze_date(*files)

    if timezone:
        for imdate in additions.values():
            imdate.timezone = timezone
    updates = {f: (v, None) for f, v in additions.items()}

    short_report = merge_report(report(files, updates, remaining))
    long_report = format_report(filter_report(short_report, '[F+]'))
    print(*long_report, sep='\n')


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

