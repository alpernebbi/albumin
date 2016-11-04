import os
import tarfile


def files_in(dir_path, relative=False):
    exclude = ['.git']
    for root, dirs, files in os.walk(dir_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude]
        if relative:
            root = os.path.relpath(root, start=relative)
        for f in files:
            yield os.path.join(root, f)


def make_tar(tar_file, dir_path):
    if not os.path.isdir(dir_path):
        raise ValueError("Folder {} doesn't exist.".format(dir_path))
    if isinstance(tar_file, str):
        with tarfile.open(name=tar_file, mode='w:gz') as tar:
            tar.add(dir_path, arcname='')
    else:
        with tarfile.open(fileobj=tar_file, mode='w:gz') as tar:
            tar.add(dir_path, arcname='')
