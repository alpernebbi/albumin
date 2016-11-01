import os
from datetime import datetime

from albumin.utils import sequenced_folder_name
from albumin.utils import files_in
from albumin.imdate import analyze_date
from albumin.imdate import ImageDate


def import_(repo, import_path, **kwargs):
    updates, remaining = get_datetime_updates(repo, import_path)
    if remaining:
        raise NotImplementedError(remaining)

    current_branch = repo.branches[0]
    repo.checkout('albumin-imports')
    repo.annex.import_(import_path)
    import_name = os.path.basename(import_path)
    batch_name = sequenced_folder_name(repo.path)
    repo.move(import_name, batch_name)
    repo.commit("Import batch {} ({})".format(batch_name, import_name))

    apply_datetime_updates(repo, updates)

    if current_branch:
        repo.checkout(current_branch)


def recheck(repo):
    current_branch = repo.branches[0]
    repo.checkout('albumin-imports')

    updates, remaining = get_datetime_updates(repo, repo.path)
    if updates:
        print("New information: ")
        for file in sorted(repo.annex.files):
            key = repo.annex.files[file]
            if key in updates:
                (datum, old) = updates[key]
                print('    {}: {} => {}'.format(file, old, datum))
                print('        (key: {})'.format(key))

    if remaining:
        print("Still no information: ")
        for file in sorted(remaining):
            print('    {}'.format(os.path.relpath(file, repo.path)))

    if current_branch:
        repo.checkout(current_branch)


def analyze(analyze_path, repo=None):
    analyze_files = list(files_in(analyze_path))
    overwrites, additions, keys = {}, {}, {}

    if repo:
        print('Compared to repo: {}'.format(repo.path))
        keys = {f: repo.annex.calckey(f) for f in analyze_files}
        updates, remaining = get_datetime_updates(repo, analyze_path)

        for file, key in keys.items():
            if key in updates:
                datum, old_datum = updates[key]
                if old_datum:
                    overwrites[file] = (datum, old_datum, key)
                else:
                    additions[file] = datum

        rem_keys = {k for f, k in keys.items() if f in remaining}
        rem_data = get_repo_datetimes(repo, rem_keys)
        for file in remaining:
            if rem_data.get(keys[file], None):
                remaining.pop(file)

    else:
        additions, remaining = analyze_date(*analyze_files)

    modified = set.union(*map(set, (overwrites, additions, remaining)))
    redundants = set(analyze_files) - modified
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


def get_datetime_updates(repo, update_path):
    files = list(files_in(update_path))
    file_data, remaining = analyze_date(*files)
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
        if datum > repo_data.get(key):
            updates[key] = (datum, repo_data.get(key))

    return updates, remaining


def apply_datetime_updates(repo, updates):
    for key, (datum, _) in updates.items():
        dt_string = datum.datetime.strftime('%Y-%m-%d@%H-%M-%S')
        repo.annex[key]['datetime'] = dt_string
        repo.annex[key]['datetime-method'] = datum.method


def get_repo_datetimes(repo, keys):
    data = {}
    for key in keys:
        dt_string = repo.annex[key]['datetime']
        method = repo.annex[key]['datetime-method']

        try:
            dt = datetime.strptime(dt_string, '%Y-%m-%d@%H-%M-%S')
            datum = ImageDate(method, dt)
            data[key] = datum
        except ValueError:
            data[key] = None
        except TypeError:
            data[key] = None

    return data
