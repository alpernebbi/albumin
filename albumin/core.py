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

    repo.checkout('albumin-imports')
    repo.annex.import_(import_path)
    import_name = os.path.basename(import_path)
    batch_name = sequenced_folder_name(repo_path)
    repo.move(import_name, batch_name)
    repo.commit("Import batch {} ({})".format(batch_name, import_name))

    if current_branch:
        repo.checkout(current_branch)


def analyze(analyze_path, **kwargs):
    results, error = analyze_date(*files_in(analyze_path))
    if error:
        print(error)

    for map_ in results.maps:
        del map_[0]
    for k in sorted(results):
        print('{}: {} ({})'.format(
            k, results[k].datetime, results[k].method))


def repo_datetimes(repo, keys):
    maps = {method: {0: method} for method in method_order}
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

    ordered_maps = [maps[method] for method in method_order]
    return ChainMap(*ordered_maps)


method_order = [
    'Manual',
    'DateTimeOriginal',
    'CreateDate']
