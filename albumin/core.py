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


def analyze(analyze_path, repo_path=None, **kwargs):
    analyze_files = list(files_in(analyze_path))
    analyze_data, remaining = analyze_date(*analyze_files)
    only_repo, same, different = {}, {}, {}

    if repo_path:
        print('Compared to repo: {}'.format(repo_path))
        repo = GitAnnexRepo(repo_path)
        analyze_keys = {f: repo.annex.calckey(f) for f in analyze_files}
        common_keys = repo.annex.keys & set(analyze_keys.values())
        repo_data = repo_datetimes(repo, common_keys)

        if repo_data:
            for file in remaining:
                key = analyze_keys[file]
                if key in repo_data:
                    only_repo[file] = repo_data[key]
                    del remaining[file]

            analyze_data = analyze_data.new_child()
            for file, value in analyze_data.items():
                key = analyze_keys[file]
                if key in repo_data:
                    if repo_data[key] == value:
                        same[file] = repo_data[key]
                        analyze_data[file] = None
                    else:
                        different[file] = (repo_data[key], value)
                        analyze_data[file] = None

            if same:
                print()
                print("Some files have metadata matching the repo:")
                for file in sorted(same):
                    print('    {}: {} ({})'.format(
                        file,
                        same[file].datetime,
                        same[file].method))

            if only_repo:
                print()
                print('Some files have metadata only in the repo:')
                for file in sorted(only_repo):
                    print('    {}: {} ({})'.format(
                        file,
                        only_repo[file].datetime,
                        only_repo[file].method))

            if different:
                print()
                print('Some files have contradictory info:')
                for file in sorted(different):
                    print('    {}: {} ({}) vs {} ({}) (repo)'.format(
                        file,
                        different[file][1].datetime,
                        different[file][1].method,
                        different[file][0].datetime,
                        different[file][0].method))

    if set(analyze_data.values()) != {None}:
        print()
        print('New files:')
        for file in sorted(analyze_data):
            if (file in same) or (file in different):
                continue
            print('    {}: {} ({})'.format(
                file,
                analyze_data[file].datetime,
                analyze_data[file].method
            ))

    if remaining:
        print()
        print("Some files have no datetime information:")
        for file in remaining:
            print('    {}'.format(file))


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
