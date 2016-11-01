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

    def __init__(self, method, datetime):
        self.method = method.split(':')[-1]
        if self.method not in ImageDate.methods:
            raise ValueError(method)
        self.datetime = datetime

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

    with ExifTool() as tool:
        tags_list = tool.get_tags_batch(exiftool_tags, file_paths)

    data = {}
    for tags in tags_list:
        file = tags['SourceFile']
        for tag, dt_string in tags.items():
            try:
                dt = datetime.strptime(dt_string, '%Y:%m:%d %H:%M:%S')
                datum = ImageDate(tag, dt)
                data[file] = max(data.get(file), datum)
            except ValueError:
                continue
    return data


def exiftool_generator(tags):
    with ExifTool() as exif_tool:
        file_path = yield None
        while file_path:
            tags_ = exif_tool.get_tags(tags, file_path)
            file_path = yield tags_


exiftool_tags = [
    'EXIF:DateTimeOriginal',
    'EXIF:CreateDate']
