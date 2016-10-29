from exiftool import ExifTool
from datetime import datetime
from collections import namedtuple


def analyze_date(file_path):
    raise NotImplementedError

ImageDate = namedtuple('ImageDate', ['path', 'method', 'datetime'])


def from_exif(*file_paths):
    with ExifTool() as tool:
        tags_list = tool.get_tags_batch(exiftool_tags, file_paths)

    for tags in tags_list:
        try:
            tag = next(tag for tag in exiftool_tags if tag in tags)
        except StopIteration:
            continue
        file = tags['SourceFile']
        datetime_ = tags[tag]

        try:
            dt = datetime.strptime(datetime_, '%Y:%m:%d %H:%M:%S')
            tag = tag.split(':')[-1]
            yield ImageDate(file, tag, dt)
        except ValueError:
            pass


def exiftool_generator(tags):
    with ExifTool() as exif_tool:
        file_path = yield None
        while file_path:
            tags_ = exif_tool.get_tags(tags, file_path)
            file_path = yield tags_


exiftool_tags = [
    'EXIF:DateTimeOriginal',
    'EXIF:CreateDate']
