from unittest import TestCase
from tests.utils import with_repo
from tests.utils import with_folder

from albumin.albumin import argument_parser
from albumin.albumin import import_


class TestAlbuminParser(TestCase):
    def setUp(self):
        self.parser = argument_parser()
        self.parse = self.parser.parse_args
        self.rpath = '/tmp/repo'
        self.ipath = '/tmp/imp'

    def test_argument_parser_help(self):
        with self.assertRaises(SystemExit) as cm:
            args = self.parse(['-h'])
        assert cm.exception.code == 0

        with self.assertRaises(SystemExit) as cm:
            args = self.parse(['--help'])
        assert cm.exception.code == 0

    def test_argument_parser_repo(self):
        args = self.parse([self.rpath])
        assert args.repo_path == self.rpath

    def test_argument_parser_no_repo(self):
        with self.assertRaises(SystemExit) as cm:
            args = self.parse(['--import', self.ipath])
        assert cm.exception.code == 2

    def test_argument_parser_import(self):
        args = self.parse([self.rpath, '--import', self.ipath])
        assert args.import_path == self.ipath

    def test_argument_parser_import_nopath(self):
        with self.assertRaises(SystemExit) as cm:
            args = self.parse([self.rpath, '--import'])
        assert cm.exception.code == 2


class TestAlbumin(TestCase):
    @with_repo(annex=True)
    @with_folder('data-tars/three-nested.tar.gz')
    def test_import_basics(self, repo, temp_folder):
        current_branch = repo.branches[0]
        import_(repo.path, temp_folder)
        assert repo.branches[0] == current_branch

        repo.checkout('albumin-imports')
        assert repo.tree_hash == \
               '3cf88503d354f1bd291d4d30cc12a023896dff09'
