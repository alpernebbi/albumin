import os
import tarfile
import re


def files_in(dir_path, relative=False):
    exclude = ['.git']
    for root, dirs, files in os.walk(dir_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude]
        if relative:
            root = os.path.relpath(root, start=relative)
        for f in files:
            yield os.path.join(root, f)


def sequenced_folder_name(parent_path):
    pattern = '\A[A-Z][0-9]{3}\Z'
    dirs = (d for d in os.listdir(parent_path) if re.match(pattern, d))
    dirs = sorted(dirs)
    if not dirs:
        return 'A000'

    last_dir = dirs[-1]
    if last_dir == 'Z999':
        raise RuntimeError('Ran out of folder names.')

    last_alpha, last_int = last_dir[0], int(last_dir[1:])
    if last_int == 999:
        next_alpha, next_int = chr(ord(last_alpha) + 1), 0
    else:
        next_alpha, next_int = last_alpha, last_int + 1

    return '{}{:03}'.format(next_alpha, next_int)


def make_tar(tar_file, dir_path):
    if not os.path.isdir(dir_path):
        raise ValueError("Folder {} doesn't exist.".format(dir_path))
    if isinstance(tar_file, str):
        with tarfile.open(name=tar_file, mode='w:gz') as tar:
            tar.add(dir_path, arcname='')
    else:
        with tarfile.open(fileobj=tar_file, mode='w:gz') as tar:
            tar.add(dir_path, arcname='')
