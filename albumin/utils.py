import os
import tarfile
import functools


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
