import os
from unittest import TestCase
from tests.utils import with_folder
from datetime import datetime

from albumin.imdate import exiftool_generator
from albumin.imdate import exiftool_tags
from albumin.imdate import from_exif
from albumin.imdate import analyze_date


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

        results = from_exif(a000)
        a000t = results[a000]
        assert a000t.method == 'DateTimeOriginal'
        assert a000t.datetime == datetime(2015, 5, 16, 14, 4, 29)

    @with_folder('data-tars/three-nested.tar.gz')
    def test_no_data(self, temp_folder):
        a = os.path.join(temp_folder, 'a.txt')
        b = os.path.join(temp_folder, 'b', 'b.txt')
        c = os.path.join(temp_folder, 'c', 'c', 'c.txt')

        results, remaining = analyze_date(a, b, c)
        assert remaining
