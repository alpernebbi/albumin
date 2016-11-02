from exiftool import ExifTool
from datetime import datetime


def analyze_date(*file_paths):
    results = from_exif(*file_paths)
    remaining = {f for f in file_paths if f not in results}
    return results, remaining


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
        return '{} ({})'.format(self.datetime, self.method)


def from_exif(*file_paths):
    if not file_paths:
        return {}

    exiftool_tags = [
        'EXIF:DateTimeOriginal',
        'EXIF:CreateDate']

    with ExifTool() as tool:
        tags_list = tool.get_tags_batch(exiftool_tags, file_paths)

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
