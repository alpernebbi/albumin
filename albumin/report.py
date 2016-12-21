# Albumin Report
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
import itertools
from collections import OrderedDict


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
        from albumin.imdate import ImageDate
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
