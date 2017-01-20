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
from albumin.imdate import Report
from albumin.utils import files_in


class AlbuminRepo(pygit2.Repository):
    @staticmethod
    def config_overrides():
        try:
            params = os.getenv('GIT_CONFIG_PARAMETERS')
            lines = params[1:-1].split("' '")
            return dict(config.split('=') for config in lines)
        except:
            return {}

    def __init__(self, path, create=False):
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

        self._session_timezone = None

    def get_config(self, key):
        value = self.config[key] if key in self.config else None
        value = self.config_overrides().get(key, value)
        return value

    @property
    def timezone(self):
        if self._session_timezone:
            return self._session_timezone
        tz = self.get_config('albumin.timezone')
        return pytz.timezone(tz) if tz else tz

    @timezone.setter
    def timezone(self, tz):
        if isinstance(tz, str):
            tz = pytz.timezone(tz)
        self._session_timezone = tz

    def import_(self, path, mtime=False, **tags):
        files = self.annex.import_(path)
        report = self.imdate_diff(
            files={self.abs_path(f): k for f, k in files.items()},
            mtime=mtime,
        )

        if report.remaining:
            raise NotImplementedError(report.remaining)

        for _, (key, new_imdate) in report.additions.items():
            self.annex[key].imdate = new_imdate
        for _, (key, new_imdate, _) in report.overwrites.items():
            self.annex[key].imdate = new_imdate
        for _, key in report.files.items():
            self.annex[key].update(tags)

        self.arrange_by_imdates(files=files)
        return report

    def analyze(self, path=None, mtime=False):
        files = {f: self.annex.calckey(f) for f in files_in(path)}
        return self.imdate_diff(files, mtime=mtime)

    def imdate_diff(self, files=None, mtime=False):
        if not files:
            files = self.new_files()
            files = {self.abs_path(f): k for f, k in files.items()}

        timezone = self.timezone
        report = analyze_date(*files, timezone=timezone, mtime=mtime)

        for file in report.remaining:
            key = files[file]
            meta = self.annex.get(key, None)
            if meta and meta.imdate:
                report.redundants[file] = key

        def conflicts(a, b):
            return a.method == b.method and a.datetime != b.datetime

        key_data = {}
        for file, (_, imdate) in report.additions.items():
            key = files[file]
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

        return Report(files, updates, report.remaining)

    def new_files(self, keys=True):
        self.index.read()
        try:
            diff = self.diff('HEAD', cached=True)
        except:
            files = (i.path for i in self.index)
        else:
            files = (
                d.delta.new_file.path for d in diff
                if d.delta.status == pygit2.GIT_STATUS_INDEX_NEW
            )

        if keys:
            return {file: self.annex.lookupkey(file) for file in files}
        else:
            return files

    def index_move(self, src, dst):
        idx = self.index[src]
        self.index.remove(src)
        idx.path = dst
        self.index.add(idx)

    def arrange_by_imdates(self, files=None, imdates=None):
        if not imdates:
            imdates = {}

        def datetime_name(file, key):
            imdate = imdates.get(key, self.annex[key].imdate)
            if not imdate:
                return None
            utc = imdate.datetime.astimezone(pytz.utc)
            ext = os.path.splitext(file)[1]
            return '{:%Y%m%dT%H%M%SZ}{{:02}}{}'.format(utc, ext)

        def move_file(file, key, dest):
            if dest in self.index:
                try:
                    dest_data = self[self.index[dest].id].data.decode()
                    dest_key = dest_data.split('/')[-1]
                    if dest_key == key:
                        self.index.remove(file)
                        return dest
                except:
                    pass

            elif not os.path.exists(self.abs_path(dest)):
                self.index_move(file, dest)
                return dest

            elif self.annex.lookupkey(dest) == key:
                self.index.remove(file)
                return dest

        if not files:
            files = self.new_files()
        moved_files = []

        self.index.read()
        for file, key in files.items():
            name_fmt = datetime_name(file, key)
            if not name_fmt:
                continue

            for i in range(0, 100):
                dest = name_fmt.format(i)

                if file == dest:
                    break
                elif move_file(file, key, dest):
                    moved_files.append(file)
                    break
            else:
                err_msg = 'Ran out of {} files'
                raise RuntimeError(err_msg.format(name_fmt))
        self.index.write()

        for file in moved_files:
            os.remove(self.abs_path(file))

        for folder in set(map(os.path.dirname, files)):
            try:
                os.removedirs(self.abs_path(folder))
            except OSError:
                pass

        self.checkout_index()
        self.annex.fix()
        self.index.read()

    def fix_filenames(self, files=None):
        if not files:
            self.index.read()
            files = (i.path for i in self.index)
        files = {f: self.annex.lookupkey(f) for f in files}
        self.arrange_by_imdates(files)

        diff = self.diff('HEAD', cached=True)
        if len(diff) > 0:
            self.commit('Fix filenames')
        return diff.stats.format(pygit2.GIT_DIFF_STATS_FULL, 80)

    def commit(self, message, timestamp=None):
        if not timestamp:
            timestamp = datetime.now(pytz.utc)

        author = pygit2.Signature(
            self.default_signature.name,
            self.default_signature.email,
            int(timestamp.timestamp())
        )

        try:
            self.head
        except pygit2.GitError:
            parents = []
        else:
            parents = [self.head.get_object().hex]

        commit = self.create_commit(
            'HEAD', author, author, message,
            self.index.write_tree(), parents
        )

        return commit

    def branch(self):
        try:
            return self.head.name
        except pygit2.GitError as err:
            msg = err.args[0]
            return msg.split('\'')[1]

    def abs_path(self, path):
        return os.path.join(self.workdir, path)

    def rel_path(self, path):
        return os.path.relpath(path, start=self.workdir)

    def __repr__(self):
        return 'AlbuminRepo(path={!r})'.format(self.path)


class AlbuminAnnex(GitAnnex):
    internal_tags = [
        'timezone', 'datetime', 'datetime-method',
        'year', 'month', 'day'
    ]

    def __init__(self, path, create=False):
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
