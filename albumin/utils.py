import os
import tarfile
import functools
import re
import collections.abc


def files_in(dir_path, relative=False):
    for root, dirs, files in os.walk(dir_path):
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


class MutualMapping(collections.abc.MutableMapping):
    def __init__(self):
        self.map_a = {}
        self.map_b = {}

    def invert(self):
        self.map_a, self.map_b = self.map_b, self.map_a
        return self

    def __getitem__(self, key):
        if key in self.map_a:
            return self.map_a[key]
        elif key in self.map_b:
            return self.map_b[key]
        else:
            raise KeyError(key)

    def __contains__(self, key):
        return key in self.map_a or key in self.map_b

    def __setitem__(self, key_a, key_b):
        for key in [key_a, key_b]:
            if key in self.map_a:
                self.map_b.pop(self.map_a.pop(key))
            if key in self.map_b:
                self.map_a.pop(self.map_b.pop(key))
        self.map_a[key_a] = key_b
        self.map_b[key_b] = key_a

    def __delitem__(self, key):
        if key in self.map_a:
            key_b = self.map_a[key]
            del self.map_b[key_b]
            del self.map_a[key]
        elif key in self.map_b:
            key_a = self.map_b[key]
            del self.map_a[key_a]
            del self.map_b[key]
        else:
            raise KeyError(key)

    def __iter__(self):
        yield from self.map_a

    def __len__(self):
        return len(self.map_a)

    def __repr__(self):
        items = '{}={{}}, ' * len(self.map_a)
        items = items.format(*self.map_a.keys())
        items = items.format(*self.map_a.values())
        return 'MutualMapping({})'.format(items[:-2])


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
