from unittest import TestCase
from argparse import ArgumentError
from tests.utils import with_repo
from tests.utils import with_folder

from albumin.cli import argument_parser


class TestAlbuminParser(TestCase):
    def setUp(self):
        self.parser = argument_parser()
        self.parse = self.parser.parse_args
        self.rpath = '/tmp/repo'
        self.ipath = '/tmp/imp'

    def test_help(self):
        with self.assertRaises(SystemExit) as cm:
            args = self.parse(['-h'])
        assert cm.exception.code == 0

        with self.assertRaises(SystemExit) as cm:
            args = self.parse(['--help'])
        assert cm.exception.code == 0

    def test_repo(self):
        args = self.parse([self.rpath])
        assert args.repo_path == self.rpath

    def test_no_repo(self):
        with self.assertRaises(SystemExit) as cm:
            args = self.parse(['--import', self.ipath])
        assert cm.exception.code == 2

    def test_import(self):
        args = self.parse([self.rpath, '--import', self.ipath])
        assert args.import_path == self.ipath

    def test_import_nopath(self):
        with self.assertRaises(SystemExit) as cm:
            args = self.parse([self.rpath, '--import'])
        assert cm.exception.code == 2

    def test_analyze_nopath(self):
        with self.assertRaises(SystemExit) as cm:
            args = self.parse([self.rpath, '--analyze'])
        assert cm.exception.code == 2

    def test_analyze_norepo(self):
        args = self.parse(['--analyze', self.ipath])

    def test_analyze_repo(self):
        args = self.parse([self.rpath, '--analyze', self.ipath])

    def test_analyze_import(self):
        with self.assertRaises(SystemExit) as cm:
            args = self.parse([self.rpath, '--analyze', self.ipath,
                               '--import', self.ipath])
        assert cm.exception.code == 2

        with self.assertRaises(SystemExit) as cm:
            args = self.parse([self.rpath, '--import', self.ipath,
                               '--analyze', self.ipath])
        assert cm.exception.code == 2
