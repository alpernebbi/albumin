import os
from unittest import TestCase
from tests.utils import with_folder
from datetime import datetime

from albumin.imdate import from_exif
from albumin.imdate import analyze_date


class TestImageDates(TestCase):
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
