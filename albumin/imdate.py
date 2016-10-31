from exiftool import ExifTool
from datetime import datetime
from collections import namedtuple
from collections import ChainMap


def analyze_date(*file_paths, chainmap=True):
    results = from_exif(*file_paths, chainmap=chainmap)
    if chainmap:
        done = results.keys()
    else:
        done_parts = (set(map_.keys()) for map_ in results.values())
        done = set.union(*done_parts)
    remaining = set(file_paths) - done

    if remaining:
        return results, remaining
    return results, None


ImageDate = namedtuple('ImageDate', ['method', 'datetime'])


def from_exif(*file_paths, chainmap=True):
    with ExifTool() as tool:
        tags_list = tool.get_tags_batch(exiftool_tags, file_paths)
    method = lambda tag : tag.split(':')[-1]

    maps = {method(tag): {} for tag in exiftool_tags}
    for tags in tags_list:
        for tag in tags:
            file = tags['SourceFile']
            datetime_ = tags[tag]

            try:
                dt = datetime.strptime(datetime_, '%Y:%m:%d %H:%M:%S')
                data = ImageDate(tag.split(':')[-1], dt)
                maps[method(tag)][file] = data
            except ValueError:
                continue

    if chainmap:
        ordered_maps = [maps[method(tag)] for tag in exiftool_tags]
        return ChainMap(*ordered_maps)
    else:
        return maps


def exiftool_generator(tags):
    with ExifTool() as exif_tool:
        file_path = yield None
        while file_path:
            tags_ = exif_tool.get_tags(tags, file_path)
            file_path = yield tags_


exiftool_tags = [
    'EXIF:DateTimeOriginal',
    'EXIF:CreateDate']
