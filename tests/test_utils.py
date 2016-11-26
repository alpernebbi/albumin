# Albumin Utils Tests
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

from unittest import TestCase
from tests.utils import with_folder
import tempfile
import os

from albumin.utils import make_tar


class TestUtils(TestCase):
    @with_folder('repo-tars/empty.tar.gz')
    def test_make_tar_file(self, temp_folder):
        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tar_file:
            make_tar(tar_file, temp_folder)

    @with_folder('repo-tars/empty.tar.gz')
    def test_make_tar_path(self, temp_folder):
        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tar_file:
            tmp_name = tar_file.name
        make_tar(tmp_name, temp_folder)
        os.remove(tmp_name)
