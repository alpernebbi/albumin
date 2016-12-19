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
import pygit2

from git_annex_adapter import GitAnnex
from git_annex_adapter import GitAnnexMetadata
from albumin.imdate import analyze_date
from albumin.imdate import ImageDate


class AlbuminRepo(pygit2.Repository):
    def __init__(self, path, create=True):
        try:
            git_path = pygit2.discover_repository(path)
        except KeyError:
            if create:
                AlbuminAnnex.init_path(path)
                git_path = pygit2.discover_repository(path)
            else:
                msg = 'Not in a git repo: {}'.format(path)
                raise ValueError(msg) from None

        super().__init__(git_path)
        self.annex = AlbuminAnnex(self.workdir, create=create)

    def imdate_diff(self, files=None, timezone=None):
        if not files:
            files = self.new_files()
            files = {self.abs_path(f): k for f, k in files.items()}

        file_data, remaining = analyze_date(*files)

        if timezone:
            for imdate in file_data.values():
                imdate.timezone = timezone

        def conflicts(a, b):
            return a.method == b.method and a.datetime != b.datetime

        key_data = {}
        for file, key in files.items():
            imdate = file_data[file]
            imdate_ = key_data.get(key, imdate)
            if conflicts(imdate, imdate_):
                raise RuntimeError(file, imdate, imdate_)
            key_data[key] = max(imdate, imdate_)

        updates = {}
        for key, new in key_data.items():
            try:
                old = self.annex.get(key).imdate
                if not new.timezone:
                    new.timezone = old.timezone
            except:
                old = None

            if (new > old) \
                    or (new == old and new.datetime != old.datetime) \
                    or (new.timezone != old.timezone):
                updates[key] = (max(new, old), old)

        return updates, remaining

    def new_files(self, keys=True):
        self.index.read()
        diff = self.diff('HEAD', cached=True)
        files = (
            d.delta.new_file.path for d in diff
            if d.delta.status == pygit2.GIT_STATUS_INDEX_NEW
        )

        if keys:
            return {file: self.annex.lookupkey(file) for file in files}
        else:
            return files

    def abs_path(self, path):
        return os.path.join(self.workdir, path)

    def rel_path(self, path):
        return os.path.relpath(path, start=self.workdir)

    def __repr__(self):
        return 'AlbuminRepo(path={!r})'.format(self.path)


class AlbuminAnnex(GitAnnex):
    def __init__(self, path, create=True):
        super().__init__(path, create=create)

    def __getitem__(self, map_key):
        metadata = super().__getitem__(map_key)
        AlbuminMetadata.make_parsed(metadata)
        return metadata

    def __repr__(self):
        return 'AlbuminAnnex(path={!r})'.format(self.path)


class AlbuminMetadata(GitAnnexMetadata):
    def __init__(self, annex, key, file=None):
        super().__init__(annex, key, file=file)

    @classmethod
    def make_parsed(cls, metadata):
        metadata.__class__ = cls

    @property
    def imdate(self):
        dt = self.get('datetime', None)
        method = self.get('datetime-method', None)
        try:
            return ImageDate(method, dt)
        except (ValueError, AttributeError):
            return None

    @imdate.setter
    def imdate(self, new):
        if not isinstance(new, ImageDate):
            raise ValueError(new)

        if new >= self.imdate:
            self['datetime'] = new.datetime
            self['datetime-method'] = new.method
            if new.timezone:
                self['timezone'] = new.timezone

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
        repr_ = 'AlbuminMetadata(key={!r}, file={!r})'
        return repr_.format(self.key, self.file)
