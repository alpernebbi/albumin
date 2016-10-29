import os
from unittest import TestCase
from tests.utils import with_folder
from datetime import datetime

from albumin.imdate import exiftool_generator
from albumin.imdate import exiftool_tags
from albumin.imdate import from_exif


class TestImageDates(TestCase):
    @with_folder(files=['images/A000.jpg'])
    def test_exif_generator(self, temp_folder):
        exgen = exiftool_generator(exiftool_tags)
        exgen.send(None)

        a000 = os.path.join(temp_folder, 'A000.jpg')
        assert os.path.isfile(a000)
        a000_tags = exgen.send(a000)
        assert a000_tags == {
            'SourceFile': a000,
            'EXIF:DateTimeOriginal': '2015:05:16 14:04:29',
            'EXIF:CreateDate': '2015:05:16 14:04:29'}

        with self.assertRaises(StopIteration):
            exgen.send(None)

    @with_folder(files=['images/A000.jpg'])
    def test_from_exif(self, temp_folder):
        a000 = os.path.join(temp_folder, 'A000.jpg')
        assert os.path.isfile(a000)

        a000t = [*from_exif(a000)][0]
        dt = datetime(2015, 5, 16, 14, 4, 29)
        assert a000t == (a000, 'EXIF:DateTimeOriginal', dt)
