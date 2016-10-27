from unittest import TestCase
from tests.utils import with_temp_folder
from tests.utils import from_tar
import tempfile
import os

from albumin.utils import make_tar


class TestUtils(TestCase):
    @with_temp_folder
    @from_tar('repo-tars/empty.tar.gz')
    def test_make_tar_file(self, cwd):
        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tar_file:
            make_tar(tar_file, cwd)

    @with_temp_folder
    @from_tar('repo-tars/empty.tar.gz')
    def test_make_tar_path(self, cwd):
        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tar_file:
            tmp_name = tar_file.name
        make_tar(tmp_name, cwd)
        os.remove(tmp_name)
