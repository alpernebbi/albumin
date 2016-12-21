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

import pytz
from exiftool import ExifTool
from datetime import datetime

from albumin.report import Report


def analyze_date(*file_paths, timezone=None):
    results = from_exif(*file_paths)
    remaining = {f for f in file_paths if f not in results}

    if timezone:
        for imdate in results.values():
            imdate.timezone = timezone

    return Report(file_paths, results, remaining)


class ImageDate:
    methods = [
        'ManualTrusted',
        'DateTimeOriginal',
        'CreateDate',
        'ManualUntrusted'
    ]

    datetime_formats = [
        '%Y:%m:%d %H:%M:%S',
        '%Y-%m-%d@%H-%M-%S'
    ]

    def __init__(self, method, datetime_):
        self.method = method.split(':')[-1]
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

    @property
    def order(self):
        return ImageDate.methods.index(self.method)

    def __lt__(self, other):
        return self.order > other.order if other else False

    def __gt__(self, other):
        return self.order < other.order if other else True

    def __eq__(self, other):
        return self.order == other.order if other else False

    def __ne__(self, other):
        return self.order != other.order if other else True

    def __le__(self, other):
        return self.order >= other.order if other else False

    def __ge__(self, other):
        return self.order <= other.order if other else True

    def __repr__(self):
        repr_ = "ImageDate(method={!r}, datetime={!r})"
        return repr_.format(self.method, self.datetime)

    def __str__(self):
        return '{:%Y-%m-%d %H:%M:%S} @ ({}) ({})'.format(
            self.datetime, self.timezone, self.method
        )


def from_exif(*file_paths):
    if not file_paths:
        return {}

    exiftool_tags = [
        'EXIF:DateTimeOriginal',
        'EXIF:CreateDate']

    with ExifTool() as tool:
        try:
            tags_list = tool.get_tags_batch(exiftool_tags, file_paths)
        except:
            tags_list = []
            for file in file_paths:
                try:
                    tags = tool.get_tags(exiftool_tags, file)
                    tags_list.append(tags)
                except:
                    pass

    data = {}
    for tags in tags_list:
        file = tags['SourceFile']
        for tag, dt in tags.items():
            try:
                datum = ImageDate(tag, dt)
                data[file] = max(data.get(file), datum)
            except ValueError:
                continue
    return data
