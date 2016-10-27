import os
import tarfile


def make_tar(tar_path, dir_path):
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        raise ValueError("Folder {} doesn't exist.".format(dir_path))
    with tarfile.open(tar_path, mode='w:gz') as tar:
        tar.add(dir_path, arcname='')
