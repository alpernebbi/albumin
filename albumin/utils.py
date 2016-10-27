import os
import tarfile
import functools


def files_in(dir_path, relative=False):
    for root, dirs, files in os.walk(dir_path):
        if relative:
            root = os.path.relpath(root, start=relative)
        for f in files:
            yield os.path.join(root, f)


@functools.singledispatch
def make_tar(tar_file, dir_path):
    with tarfile.open(fileobj=tar_file, mode='w:gz') as tar:
        tar.add(dir_path, arcname='')


@make_tar.register(str)
def _(tar_file, dir_path):
    if not os.path.isdir(dir_path):
        raise ValueError("Folder {} doesn't exist.".format(dir_path))
    with tarfile.open(tar_file, mode='w:gz') as tar:
        tar.add(dir_path, arcname='')
