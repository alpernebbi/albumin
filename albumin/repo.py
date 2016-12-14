# Albumin Repo
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
from datetime import datetime
from datetime import tzinfo
import pytz

from git_annex_adapter import GitAnnex
from git_annex_adapter import GitAnnexMetadata
from git_annex_adapter import RepeatedProcess


class AlbuminRepo:
    def __init__(self, path, create=True):
        self.annex = AlbuminAnnex(path, create=create)

        git = RepeatedProcess('git', workdir=path)
        root_path = git('rev-parse', '--show-toplevel').strip()

        git._workdir = root_path
        self.path = root_path
        self._git = git

    @property
    def status(self):
        return self._git('status', '-s')

    @property
    def branches(self):
        branch_list = []
        current_exists = False
        for branch in self._git('branch', '--list').splitlines():
            if branch[0] == '*':
                branch_list.insert(0, branch[2:])
                current_exists = True
            else:
                branch_list.append(branch[2:])
        if branch_list and not current_exists:
            raise RuntimeError(
                'No current branch found among: \n'
                '    {}\n    in {}'.format(branch_list, self.path))
        return tuple(branch_list)

    def add(self, path):
        return self._git('add', path)

    def rm(self, path):
        return self._git('rm', '-rf', path)

    def move(self, src, dest, overwrite=False, merge=True):
        abs_src = os.path.join(self.path, src)
        abs_dest = os.path.join(self.path, dest)

        def files_in(dir_path):
            exclude = ['.git']
            for root, dirs, files in os.walk(dir_path, topdown=True):
                dirs[:] = [d for d in dirs if d not in exclude]
                relative_root = os.path.relpath(root, start=self.path)
                for f in files:
                    yield os.path.join(relative_root, f)

        if os.path.isdir(abs_src) and os.path.isdir(abs_dest) and merge:
            for src_ in files_in(abs_src):
                dest_ = os.path.join(dest, os.path.relpath(src_, src))
                self.move(src_, dest_, overwrite=overwrite)
            return

        if os.path.isfile(abs_dest):
            if os.path.samefile(abs_src, abs_dest) or overwrite:
                self._git('rm', dest)
            else:
                raise ValueError(
                    "Destination {} already exists.".format(dest))

        abs_dest_dir = os.path.dirname(abs_dest)
        os.makedirs(abs_dest_dir, exist_ok=True)
        self._git('mv', src, dest)

        abs_src_dir = os.path.dirname(abs_src)
        if not os.listdir(abs_src_dir):
            os.removedirs(abs_src_dir)

    def checkout(self, branch, new_branch=True):
        command = ['checkout', branch]
        if new_branch and branch not in self.branches:
            command.insert(1, '-b')
        return self._git(*command)

    def commit(self, message, add=True, allow_empty=False):
        command = ['commit', '-m', message]
        if add: command.append('-a')
        if allow_empty: command.append('--allow-empty')
        return self._git(*command)

    def cherry_pick(self, branch):
        return self._git("cherry-pick", branch)

    def stash(self, pop=False):
        command = ['stash']
        if pop: command.append('pop')
        return self._git(*command)

    @property
    def tree_hash(self):
        commit = self._git('cat-file', 'commit', 'HEAD').split()
        return commit[commit.index('tree') + 1]

    def __repr__(self):
        return 'GitRepo(path={!r})'.format(self.path)


class AlbuminAnnex(GitAnnex):
    def __init__(self, path, create=True):
        super().__init__(path, create=create)

    def __getitem__(self, map_key):
        metadata = super().__getitem__(map_key)
        AlbuminMetadata.make_parsed(metadata)
        return metadata


class AlbuminMetadata(GitAnnexMetadata):
    def __init__(self, annex, key, file=None):
        super().__init__(annex, key, file=file)

    @classmethod
    def make_parsed(cls, metadata):
        metadata.__class__ = cls

    def __getitem__(self, meta_key):
        try:
            value = super().__getitem__(meta_key)[0]
        except IndexError:
            raise KeyError(meta_key)

        if meta_key == 'datetime':
            dt_naive = datetime.strptime(value, '%Y-%m-%d@%H-%M-%S')
            dt_utc = pytz.utc.localize(dt_naive)
            timezone = self.get('timezone', pytz.utc)
            value = dt_utc.astimezone(timezone)

        elif meta_key.endswith('lastchanged'):
            dt_naive = datetime.strptime(value, '%Y-%m-%d@%H-%M-%S')
            value = pytz.utc.localize(dt_naive)

        elif meta_key == 'timezone':
            value = pytz.timezone(value)

        return value

    def __setitem__(self, meta_key, value):
        if isinstance(value, datetime):
            value_utc = value.astimezone(pytz.utc)
            value = value_utc.strftime('%Y-%m-%d@%H-%M-%S')

        elif isinstance(value, tzinfo):
            value = value.tzname(None)

        if meta_key == 'datetime':
            year, month, day = value[:4], value[5:7], value[8:10]
            super().__setitem__('year', [year])
            super().__setitem__('month', [month])
            super().__setitem__('day', [day])

        super().__setitem__(meta_key, [value])

    def __repr__(self):
        repr_ = 'GitAnnexParsedMetadata(key={!r}, path={!r})'
        return repr_.format(self.key, self.annex.repo.path)
