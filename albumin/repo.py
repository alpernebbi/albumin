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

from datetime import datetime
from datetime import tzinfo
import pytz

from git_annex_adapter import GitRepo
from git_annex_adapter import GitAnnex
from git_annex_adapter import GitAnnexMetadata


class AlbuminRepo(GitRepo):
    def __init__(self, path, create=True):
        super().__init__(path, create=create)
        self.annex = AlbuminAnnex(self, create=create)

    @classmethod
    def make_annex(cls, repo, create=False):
        repo.annex = AlbuminAnnex(repo, create=create)
        repo.__class__ = cls

    def __repr__(self):
        return 'GitAnnexRepo(path={!r})'.format(self.path)


class AlbuminAnnex(GitAnnex):
    def __init__(self, repo, create=True):
        super().__init__(repo, create=create)

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
