# Albumin Imdate
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
import pytz
import itertools
from exiftool import ExifTool
from datetime import datetime
from collections import OrderedDict

from albumin.lexical_ordering import lexical_ordering


def analyze_date(*paths, timezone=None):
    results = from_exif(*paths)
    remaining = {f for f in paths if f not in results}

    for imdate in results.values():
        if timezone and not imdate.timezone:
            imdate.timezone = timezone

    return Report(paths, results, remaining)


def from_exif(*paths):
    if not paths:
        return {}

    exiftool_tags = [
        'EXIF:DateTimeOriginal',
        'MakerNotes:DateTimeOriginal',
        'EXIF:CreateDate',
        'MakerNotes:CreateDate',
    ]

    with ExifTool() as tool:
        try:
            tags_list = tool.get_tags_batch(exiftool_tags, paths)
        except:
            tags_list = []
            for file in paths:
                try:
                    tags = tool.get_tags(exiftool_tags, file)
                    tags_list.append(tags)
                except:
                    pass

    imdates = {}
    for tags in tags_list:
        file = tags['SourceFile']
        for tag, dt in tags.items():
            try:
                tag = 'ExifTool/' + tag.replace(':', '/')
                imdate = ImageDate(tag, dt)
                imdates[file] = max(imdates.get(file), imdate)
            except ValueError:
                continue
    return imdates


@lexical_ordering
class ImageDate:
    methods = [
        'Manual/Trusted',
        'ExifTool/EXIF/DateTimeOriginal',
        'ExifTool/MakerNotes/DateTimeOriginal',
        'ExifTool/EXIF/CreateDate',
        'ExifTool/MakerNotes/CreateDate',
        'Manual/Untrusted'
    ]

    datetime_formats = [
        '%Y:%m:%d %H:%M:%S',
        '%Y-%m-%d@%H-%M-%S'
    ]

    def __init__(self, method, datetime_):
        self.method = method
        if self.method not in ImageDate.methods:
            raise ValueError(method)

        if isinstance(datetime_, datetime):
            self.datetime = datetime_
        else:
            for fmt_ in ImageDate.datetime_formats:
                try:
                    self.datetime = datetime.strptime(datetime_, fmt_)
                    break
                except (ValueError, TypeError):
                    continue
            else:
                raise ValueError(datetime_)

    @classmethod
    def parse(cls, imdate_str):
        datetime_, info = imdate_str.split(' @ ')
        timezone, method = info.strip('()').split(') (')
        datetime_ = datetime.strptime(datetime_, '%Y-%m-%d %H:%M:%S')
        datetime_ = pytz.timezone(timezone).localize(datetime_)
        return cls(method, datetime_)

    @property
    def timezone(self):
        try:
            return self.datetime.tzinfo.tzname(None)
        except:
            return None

    @timezone.setter
    def timezone(self, tz):
        if tz is None:
            return

        if isinstance(tz, str):
            tz = pytz.timezone(tz)

        if self.timezone:
            self.datetime = self.datetime.astimezone(tz)
        else:
            self.datetime = tz.localize(self.datetime)

    def lexical_key(self):
        return -ImageDate.methods.index(self.method)

    def __lt__(self, other):
        return False if other is None else NotImplemented

    def __gt__(self, other):
        return True if other is None else NotImplemented

    def __eq__(self, other):
        return False if other is None else NotImplemented

    def __ne__(self, other):
        return True if other is None else NotImplemented

    def __le__(self, other):
        return False if other is None else NotImplemented

    def __ge__(self, other):
        return True if other is None else NotImplemented

    def __repr__(self):
        repr_ = "ImageDate(method={!r}, datetime={!r})"
        return repr_.format(self.method, self.datetime)

    def __str__(self):
        return '{:%Y-%m-%d %H:%M:%S} @ ({}) ({})'.format(
            self.datetime, self.timezone, self.method
        )


class Report(object):
    sections = {
        '[K?]': 'No Information:',
        '[K+]': 'New Keys:',
        '[K!]': 'Updated Keys:',
        '[K=]': 'Redundant Keys:',
        '[F?]': 'No Information:',
        '[F+]': 'New Files:',
        '[F!]': 'Updated Files:',
        '[F=]': 'Redundant Files:',
    }

    @staticmethod
    def sorted_dict(d):
        def sort_key(t):
            path, _ = t
            return os.path.split(path)
        return OrderedDict(sorted(d.items(), key=sort_key))

    def __init__(self, files, updates, remaining):
        self.overwrites = OrderedDict()
        self.additions = OrderedDict()
        self.redundants = OrderedDict()

        try:
            files.items()
            self.has_keys = True
        except AttributeError:
            files = {f: f for f in files}
            self.has_keys = False

        self.files = self.sorted_dict(files)

        try:
            _, (_, _) = next(iter(updates.items()))
        except (TypeError, ValueError):
            updates = {f: (v, None) for f, v in updates.items()}
        except StopIteration:
            pass

        for file, key in self.files.items():
            new, old = updates.get(key, (None, None))
            if new and old:
                self.overwrites[file] = (key, new, old)
            elif new:
                self.additions[file] = (key, new)
            elif file not in remaining:
                self.redundants[file] = key

    @classmethod
    def parse(cls, report_lines):
        def prefix(line):
            return line[:4]

        lines = list(report_lines)
        breaks = map(cls.sections.__contains__, map(prefix, lines))
        group_nums = list(itertools.accumulate(map(int, breaks)))
        groups = OrderedDict((i, []) for i in group_nums)

        for line, num in zip(lines, group_nums):
            groups[num].append(line)

        files, updates, remaining = {}, {}, {}

        for group in groups.values():
            info = {}
            for num, line in enumerate(group):
                info[prefix(line)] = line[5:] if num == 0 else line[8:]

            new, old = info.get('[ T]'), info.get('[ t]')
            new = ImageDate.parse(new) if new else new
            old = ImageDate.parse(old) if old else old

            key = info.get('[K?]') or info.get('[K!]') \
                  or info.get('[K+]') or info.get('[K=]')

            file = info.get('[F?]') or info.get('[F!]') \
                   or info.get('[F+]') or info.get('[F=]')

            if key:
                file = info.get('[ F]')
            elif file:
                key = file

            if '[K?]' in info or '[F?]' in info:
                files[file], remaining[file] = key, key

            elif '[K!]' in info or '[F!]' in info \
                    or '[K+]' in info or '[F+]' in info:
                files[file], updates[key] = key, (new, old)

            elif '[K=]' in info or '[F=]' in info:
                files[file] = key

        report = Report(files, updates, remaining)

        if all(file == key for file, key in files.items()):
            report.has_keys = False

        return report

    @property
    def updates(self):
        value = {}
        for file, (key, new, old) in self.overwrites.items():
            value[key] = (new, old)
        for file, (key, new) in self.additions.items():
            value[key] = (new, None)
        return value

    @property
    def remaining(self):
        valid = {*self.additions, *self.overwrites, *self.redundants}
        return OrderedDict(
            (file, key) for (file, key) in self.files.items()
            if file not in valid
        )

    def short(self):
        if self.has_keys:
            for file, key in self.remaining.items():
                yield '[K?] {}'.format(key)
                yield '[ F] :: {}'.format(file)

            for file, (key, new, old) in self.overwrites.items():
                yield '[K!] {}'.format(key)
                yield '[ F] :: {}'.format(file)
                yield '[ T] :: {}'.format(new)
                yield '[ t] :: {}'.format(old)

            for file, (key, new) in self.additions.items():
                yield '[K+] {}'.format(key)
                yield '[ F] :: {}'.format(file)
                yield '[ T] :: {}'.format(new)

            for file, key in self.redundants.items():
                yield '[K=] {}'.format(key)
                yield '[ F] :: {}'.format(file)

        else:
            for file, _ in self.remaining.items():
                yield '[F?] {}'.format(file)

            for file, (_, new, old) in self.overwrites.items():
                yield '[F!] {}'.format(file)
                yield '[ T] :: {}'.format(new)
                yield '[ t] :: {}'.format(old)

            for file, (_, new) in self.additions.items():
                yield '[F+] {}'.format(file)
                yield '[ T] :: {}'.format(new)

            for file, _ in self.redundants.items():
                yield '[F=] {}'.format(file)

    def long(self):
        current = None

        for line in self.short():
            prefix = line[:4]
            section = self.sections.get(prefix, current)

            if current != section:
                if current:
                    yield ''
                current = section
                yield current

            yield '  ' + line[5:]

    def __str__(self):
        return "\n".join(self.long())

    def __repr__(self):
        return (
            'Report('
            + 'has_keys={}, '.format(self.has_keys)
            + 'files={}, '.format(self.files)
            + 'overwrites={}, '.format(self.overwrites)
            + 'additions={}, '.format(self.additions)
            + 'redundants={}, '.format(self.redundants)
            + 'remaining={}'.format(self.remaining)
            + ')'
        )