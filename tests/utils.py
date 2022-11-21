# Albumin Test Utilities
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

import tempfile
import functools
import tarfile
import shutil

from albumin.repo import AlbuminRepo


def with_folder(tar_path=None, files=None, param='temp_folder'):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with tempfile.TemporaryDirectory() as temp_folder:
                if tar_path:
                    with tarfile.open(tar_path) as tar:
                        
                        import os
                        
                        def is_within_directory(directory, target):
                            
                            abs_directory = os.path.abspath(directory)
                            abs_target = os.path.abspath(target)
                        
                            prefix = os.path.commonprefix([abs_directory, abs_target])
                            
                            return prefix == abs_directory
                        
                        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                        
                            for member in tar.getmembers():
                                member_path = os.path.join(path, member.name)
                                if not is_within_directory(path, member_path):
                                    raise Exception("Attempted Path Traversal in Tar File")
                        
                            tar.extractall(path, members, numeric_owner=numeric_owner) 
                            
                        
                        safe_extract(tar, path=temp_folder)
                if files:
                    for file in files:
                        shutil.copy2(file, temp_folder)
                kwargs[param] = temp_folder
                return func(*args, **kwargs)
        return wrapper
    return decorator


def with_repo(tar_path=None, annex=False, param='repo'):
    def decorator(func):
        @functools.wraps(func)
        @with_folder(tar_path, param='repo_path')
        def wrapper(*args, **kwargs):
            repo = AlbuminRepo(kwargs['repo_path'])
            del kwargs['repo_path']
            kwargs[param] = repo
            try:
                return func(*args, **kwargs)
            finally:
                if annex:
                    repo.annex._annex('uninit')
        return wrapper
    return decorator
