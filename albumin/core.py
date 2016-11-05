import os
import pytz
from datetime import datetime

from albumin.utils import files_in
from albumin.imdate import analyze_date
from albumin.imdate import ImageDate


def import_(repo, import_path, timezone=None, tags=None):
    current_branch = repo.branches[0]

    updates, remaining = get_datetime_updates(
        repo, import_path, timezone=timezone)
    if remaining:
        raise NotImplementedError(remaining)
    if not updates:
        print('All files and info already in repo.')
        return

    album_keys = set()

    repo.checkout('albumin')
    timestamp = datetime.now(pytz.utc).strftime('%Y%m%dT%H%M%SZ')
    album_record_path = os.path.join(repo.path, timestamp + '.txt')
    with open(album_record_path, 'xt') as album_record:
        print('# path: {}'.format(import_path), file=album_record)
        print('# timezone: {}'.format(timezone), file=album_record)
        if tags:
            for tag, value in tags.items():
                print('# {}: {}'.format(tag, value), file=album_record)
        for path in sorted(files_in(import_path)):
            key = repo.annex.calckey(path)
            album_keys.add(key)
            relpath = os.path.relpath(path, import_path)
            print('{}: {}'.format(key, relpath), file=album_record)
    repo.add(timestamp + '.txt')
    import_name = os.path.basename(import_path)
    album_name = tags.get('album', import_name)
    repo.commit('Record album {}'.format(album_name))

    repo.checkout('master')
    repo.annex.import_(import_path)
    repo.rm(import_name)

    apply_datetime_updates(repo, updates, timezone=timezone)

    for key in album_keys:
        meta = repo.annex[key]
        if tags:
            for tag, value in tags.items():
                meta[tag] = value
        extension = os.path.splitext(key)[1]
        dt = meta['datetime'].astimezone(pytz.utc)
        dt = dt.strftime('%Y%m%dT%H%M%SZ')
        for i in range(0, 100):
            new_name = '{}{:02}{}'.format(dt, i, extension)
            new_path = os.path.join(album_name, new_name)
            new_abs_path = os.path.join(repo.path, new_path)
            if not os.path.exists(new_abs_path):
                repo.annex.fromkey(key, new_path)
                break
            elif repo.annex.lookupkey(new_path) == key:
                break
        else:
            err_msg = 'Ran out of {}xx{} files'
            raise RuntimeError(err_msg.format(dt, extension))
    repo.add(album_name)
    repo.commit('Import album {}'.format(album_name))

    repo.checkout(current_branch)


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

    common_keys = repo.annex.keys & set(data)
    repo_data = get_repo_datetimes(repo, common_keys)

    updates = {}
    for key, datum in data.items():
        old_datum = repo_data.get(key)
        if not timezone:
            timezone_ = repo.annex[key].get('timezone', pytz.utc)
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
        meta = repo.annex[key]
        dt = meta['datetime']
        method = meta['datetime-method']
        try:
            data[key] = ImageDate(method, dt)
        except ValueError:
            data[key] = None
    return data
