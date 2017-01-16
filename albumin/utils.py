# Albumin Utils
# Copyright (C) 2016 Alper Nebi Yasak
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import tarfile
from exiftool import ExifTool


def exiftool_tags(*paths):
    with ExifTool() as tool:
        tags_list = tool.get_tags_batch([], paths)

    tags_dict = {}
    for tags in tags_list:
        file = tags.pop('SourceFile')
        tags_dict[file] = tags
    return tags_dict


def files_in(dir_path, relative=False):
    if (dir_path is None) or (not os.path.isdir(dir_path)):
        return
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
