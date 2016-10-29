from unittest import TestCase
from tests.utils import with_repo
from tests.utils import with_folder

from albumin.core import import_


class TestAlbuminCore(TestCase):
    @with_repo(annex=True)
    @with_folder('data-tars/three-nested.tar.gz')
    def test_import_basics(self, repo, temp_folder):
        current_branch = repo.branches[0]
        import_(repo.path, temp_folder)
        assert repo.branches[0] == current_branch

        repo.checkout('albumin-imports')
        assert repo.tree_hash == \
               '3cf88503d354f1bd291d4d30cc12a023896dff09'
