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

from albumin.utils import files_in
from albumin.imdate import analyze_date


def import_(repo, import_path, timezone=None, tags=None):
    if not tags:
        tags = {}

    timestamp = datetime.now(pytz.utc)
    batch = '{:%Y%m%dT%H%M%SZ}'.format(timestamp)

    imported_files = repo.annex.import_(import_path)
    repo.annex.clear_metadata_cache()
    import_dest = os.path.join(
        repo.workdir, os.path.basename(import_path)
    )

    updates, remaining = get_datetime_updates(
        repo,
        {os.path.join(repo.workdir, f): k
         for f, k in imported_files.items()},
        timezone=timezone
    )
    if remaining:
        raise NotImplementedError(remaining)
    if not updates:
        print('All files and info already in repo.')
        return

    for key, (new_imdate, _) in updates.items():
        repo.annex[key].imdate = new_imdate

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
            repo, keys, timezone=timezone)

        for file, key in keys.items():
            if key in updates:
                datum, old_datum = updates[key]
                if old_datum:
                    overwrites[file] = (datum, old_datum, key)
                else:
                    additions[file] = datum

        rem_keys = {k for f, k in keys.items() if f in remaining}
        rem_data = {key: repo.annex[key].imdate for key in rem_keys}
        for file in remaining.copy():
            if rem_data.get(keys[file], None):
                remaining.remove(file)
    else:
        additions, remaining = analyze_date(*files)
        if timezone:
            for imdate in additions.values():
                imdate.timezone = timezone

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


def get_datetime_updates(repo, files, timezone=None):
    file_data, remaining = analyze_date(*files)

    if timezone:
        for imdate in file_data.values():
            imdate.timezone = timezone

    def conflicts(a, b):
        return a.method == b.method and a.datetime != b.datetime

    key_data = {}
    for file, key in files.items():
        imdate = file_data[file]
        imdate_ = key_data.get(key, imdate)
        if conflicts(imdate, imdate_):
            raise RuntimeError(file, imdate, imdate_)
        key_data[key] = max(imdate, imdate_)

    updates = {}
    for key, new in key_data.items():
        try:
            old = repo.annex.get(key).imdate
            if not new.timezone:
                new.timezone = old.timezone
        except:
            old = None

        if (new > old) \
                or (new == old and new.datetime != old.datetime) \
                or (new.timezone != old.timezone):
            updates[key] = (max(new, old), old)

    return updates, remaining
