from unittest import TestCase

from albumin.albumin import argument_parser


class TestAlbumin(TestCase):
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

