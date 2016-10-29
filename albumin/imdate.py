from exiftool import ExifTool
from datetime import datetime
from collections import namedtuple
from collections import ChainMap


def analyze_date(*file_paths):
    results = from_exif(*file_paths)
    remaining = [f for f in file_paths if f not in results]

    if remaining:
        return results, NotImplementedError(
            "No datetime information found about some files:\n" \
            + ("    {}\n" * len(remaining)).format(*remaining)
        )
    return results, None


ImageDate = namedtuple('ImageDate', ['method', 'datetime'])


def from_exif(*file_paths):
    with ExifTool() as tool:
        tags_list = tool.get_tags_batch(exiftool_tags, file_paths)

    maps = {tag: {0: tag.split(':')[-1]} for tag in exiftool_tags}
    for tags in tags_list:
        for tag in tags:
            file = tags['SourceFile']
            datetime_ = tags[tag]

            try:
                dt = datetime.strptime(datetime_, '%Y:%m:%d %H:%M:%S')
                data = ImageDate(tag.split(':')[-1], dt)
                maps[tag][file] = data
            except ValueError:
                continue

    ordered_maps = [maps[tag] for tag in exiftool_tags]
    return ChainMap(*ordered_maps)


def exiftool_generator(tags):
    with ExifTool() as exif_tool:
        file_path = yield None
        while file_path:
            tags_ = exif_tool.get_tags(tags, file_path)
            file_path = yield tags_


exiftool_tags = [
    'EXIF:DateTimeOriginal',
    'EXIF:CreateDate']
