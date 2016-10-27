from unittest import TestCase
from tests.utils import with_temp_folder
from tests.utils import from_tar
import tempfile

from albumin.utils import make_tar


class TestUtils(TestCase):
    @with_temp_folder
    @from_tar('repo-empty.tar.gz')
    def test_make_tar(self, cwd):
        with tempfile.TemporaryFile() as tar_file:
            make_tar(tar_file, cwd)
