import os
from datetime import datetime
from collections import ChainMap

from albumin.gitrepo import GitAnnexRepo
from albumin.utils import sequenced_folder_name
from albumin.utils import files_in
from albumin.imdate import analyze_date
from albumin.imdate import ImageDate


def import_(repo_path, import_path, **kwargs):
    repo = GitAnnexRepo(repo_path)
    current_branch = repo.branches[0]

    import_files = list(files_in(import_path))
    import_file_data, err = analyze_date(*import_files, chainmap=False)
    import_keys = {f: repo.annex.calckey(f) for f in import_files}
    if err:
        raise err

    import_data = {}
    for method, map_ in import_file_data.items():
        import_data[method] = {}
        for file, data in map_.items():
            key = import_keys[file]
            if import_data[method].get(key, data) != data:
                err_msg = ('Multiple results for same file: {} '
                           'has {} and {}.')
                err_msg = err_msg.format(key, import_data[key], data)
                raise RuntimeError(err_msg)
            import_data[method][key] = data

    repo.checkout('albumin-imports')
    repo.annex.import_(import_path)
    import_name = os.path.basename(import_path)
    batch_name = sequenced_folder_name(repo_path)
    repo.move(import_name, batch_name)
    repo.commit("Import batch {} ({})".format(batch_name, import_name))

    common_keys = repo.annex.keys & set(import_keys.values())
    repo_data = repo_datetimes(repo, common_keys, chainmap=False)

    chain = []
    for method in method_order:
        chain.append(import_data.get(method, {}))
        chain.append(repo_data.get(method, {}))
    final_data = ChainMap(*chain)

    repo_chain = ChainMap(*[repo_data[m] for m in method_order])

    for key, data in final_data.items():
        if repo_chain.get(key, None) != data:
            dt_string = data.datetime.strftime('%Y-%m-%d@%H-%M-%S')
            repo.annex[key]['datetime'] = dt_string
            repo.annex[key]['datetime-method'] = data.method

    if current_branch:
        repo.checkout(current_branch)


def analyze(analyze_path, **kwargs):
    results, error = analyze_date(*files_in(analyze_path))
    if error:
        print(error)

    for k in sorted(results):
        print('{}: {} ({})'.format(
            k, results[k].datetime, results[k].method))


def repo_datetimes(repo, keys, chainmap=True):
    maps = {method: {} for method in method_order}
    for key in keys:
        dt_string = repo.annex[key]['datetime']
        method = repo.annex[key]['datetime-method']

        try:
            dt = datetime.strptime(dt_string, '%Y-%m-%d@%H-%M-%S')
            data = ImageDate(method, dt)
            maps[method][key] = data
        except ValueError:
            continue
        except TypeError:
            continue

    if chainmap:
        ordered_maps = [maps[method] for method in method_order]
        return ChainMap(*ordered_maps)
    else:
        return maps


method_order = [
    'Manual',
    'DateTimeOriginal',
    'CreateDate']
