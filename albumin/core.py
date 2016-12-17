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
from albumin.imdate import ImageDate


def import_(repo, import_path, timezone=None, tags=None):
    if not tags:
        tags = {}

    updates, remaining = get_datetime_updates(
        repo, import_path, timezone=timezone)
    if remaining:
        raise NotImplementedError(remaining)
    if not updates:
        print('All files and info already in repo.')
        return

    timestamp = datetime.now(pytz.utc)
    batch = '{:%Y%m%dT%H%M%SZ}'.format(timestamp)

    repo.annex.import_(import_path)
    repo.annex.clear_metadata_cache()
    import_dest = os.path.join(
        repo.workdir, os.path.basename(import_path)
    )
    imported_files = OrderedDict(
        (path, repo.annex.lookupkey(path))
        for path in sorted(files_in(import_dest, relative=repo.workdir))
    )

    apply_datetime_updates(repo, updates, timezone=timezone)

    for key in imported_files.values():
        meta = repo.annex[key]
        meta.update(**tags, batch=batch)
        extension = os.path.splitext(key)[1]
        dt = meta['datetime'].astimezone(pytz.utc)
        dt = dt.strftime('%Y%m%dT%H%M%SZ')
        for i in range(0, 100):
            new_name = '{}{:02}{}'.format(dt, i, extension)
            new_path = os.path.join(batch, new_name)
            new_abs_path = os.path.join(repo.workdir, new_path)
            if not os.path.exists(new_abs_path):
                repo.annex.fromkey(key, new_path)
                break
            elif repo.annex.lookupkey(new_path) == key:
                break
        else:
            err_msg = 'Ran out of {}xx{} files'
            raise RuntimeError(err_msg.format(dt, extension))

    repo.index.read()
    for file in imported_files:
        repo.index.remove(file)
        os.remove(os.path.join(repo.workdir, file))
    os.removedirs(import_dest)
    repo.index.add_all([batch])
    repo.index.write()
    repo.annex.clear_metadata_cache()

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
        'Imported files: ',
        *('{}: {}'.format(key, path)
          for path, key in imported_files.items()
        ),
        '',
        'Updates: ',
        *('{}: {} => {}'.format(key, old, new) if old
          else '{}: {}'.format(key, new)
          for key, (new, old) in updates.items()
        ),
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
    overwrites, additions, keys = {}, {}, {}

    if repo:
        print('Compared to repo: {}'.format(repo.path))
        keys = {f: repo.annex.calckey(f) for f in files}
        updates, remaining = get_datetime_updates(
            repo, analyze_path, timezone=timezone)

        for file, key in keys.items():
            if key in updates:
                datum, old_datum = updates[key]
                if old_datum:
                    overwrites[file] = (datum, old_datum, key)
                else:
                    additions[file] = datum

        rem_keys = {k for f, k in keys.items() if f in remaining}
        rem_data = get_repo_datetimes(repo, rem_keys)
        for file in remaining.copy():
            if rem_data.get(keys[file], None):
                remaining.remove(file)
    else:
        additions, remaining = analyze_date(*files, timezone=timezone)

    modified = set.union(*map(set, (overwrites, additions, remaining)))
    redundants = set(files) - modified
    if redundants:
        print("No new information: ")
        for file in sorted(redundants):
            print('    {}'.format(file))

    if additions:
        print("New files: ")
        for file in sorted(additions):
            datum = additions[file]
            print('    {}: {}'.format(file, datum))

    if overwrites:
        print("New information: ")
        for file in sorted(overwrites):
            (datum, old_datum, key) = overwrites[file]
            print('    {}: {} => {}'.format(file, old_datum, datum))
            print('        (from {})'.format(key))

    if remaining:
        print("No information: ")
        for file in sorted(remaining):
            print('    {}'.format(file))


def get_datetime_updates(repo, update_path, timezone=None):
    files = list(files_in(update_path))
    file_data, remaining = analyze_date(*files, timezone=timezone)
    keys = {f: repo.annex.calckey(f) for f in files}

    def conflict_error(key, data_1, data_2):
        err_msg = ('Conflicting results for file: \n'
                   '    {}:\n    {} vs {}.')
        return RuntimeError(err_msg.format(key, data_1, data_2))

    data = {}
    for file, datum in file_data.items():
        key = keys[file]
        if key in data and data[key] == datum:
            if data[key].datetime != datum.datetime:
                raise conflict_error(key, data[key], data)
        data[key] = max(data.get(key), datum)

    common_keys = repo.annex.keys() & set(data)
    repo_data = get_repo_datetimes(repo, common_keys)

    updates = {}
    for key, datum in data.items():
        old_datum = repo_data.get(key)
        if not timezone:
            metadata = repo.annex.get(key, {})
            timezone_ = metadata.get('timezone', pytz.utc)
            datum.datetime = timezone_.localize(datum.datetime)
        if datum != old_datum or datum.datetime != old_datum.datetime:
            updates[key] = (datum, repo_data.get(key))
    return updates, remaining


def apply_datetime_updates(repo, updates, timezone=None):
    for key, (datum, _) in updates.items():
        meta = repo.annex[key]
        meta['datetime'] = datum.datetime
        meta['datetime-method'] = datum.method
        if timezone:
            meta['timezone'] = timezone


def get_repo_datetimes(repo, keys):
    data = {}
    for key in keys:
        try:
            meta = repo.annex[key]
            dt = meta['datetime']
            method = meta['datetime-method']
            data[key] = ImageDate(method, dt)
        except (ValueError, KeyError, AttributeError):
            data[key] = None
    return data
