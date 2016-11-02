#!/usr/bin/env python3
import argparse
import albumin.core
from albumin.gitrepo import GitAnnexRepo


def main(*args):
    parser = argument_parser()
    ns = parser.parse_args(*args)
    validate_namespace(ns)

    if ns.repo_path:
        repo = GitAnnexRepo(ns.repo_path)
        ns.repo = repo
        del ns.repo_path
    else:
        ns.repo = None

    if ns.import_path:
        albumin.core.import_(ns.repo,
                             ns.import_path)
    elif ns.analyze_path:
        albumin.core.analyze(ns.analyze_path,
                             repo=ns.repo)
    elif ns.recheck_repo:
        albumin.core.recheck(ns.repo,
                             apply=ns.apply)


def argument_parser():
    parser = argparse.ArgumentParser(
        description="Manage photographs using a git-annex repository.",
        usage='%(prog)s [repo-path] [action [option ...]]',
        add_help=False)

    positional = parser.add_argument_group('Positional arguments')

    positional.add_argument(
        'repo_path',
        metavar='repo-path',
        nargs='?',
        help="path of the git-annex repository")

    actions = parser.add_argument_group('Actions')

    actions.add_argument(
        '--help', '-h',
        action='help',
        help='show this help message and exit')

    actions.add_argument(
        '--import',
        dest="import_path",
        metavar="path",
        help="import pictures from the given path")

    actions.add_argument(
        '--analyze',
        dest="analyze_path",
        action='store',
        metavar="path",
        help="analyze pictures in the given path")

    actions.add_argument(
        '--recheck',
        dest="recheck_repo",
        action='store_true',
        help="recheck files in repo for new metadata")

    options = parser.add_argument_group('Options')

    options.add_argument(
        '--apply',
        dest='apply',
        action='store_true',
        help="apply new metadata from recheck")

    return parser


def validate_namespace(ns):
    if ns.import_path:
        if not ns.repo_path:
            raise ValueError(
                'Repository required for --import.')
        if ns.analyze_path or ns.recheck_repo:
            raise ValueError(
                'Multiple actions are forbidden.')

    if ns.analyze_path:
        if ns.import_path or ns.recheck_repo:
            raise ValueError(
                'Multiple actions are forbidden.')

    if ns.recheck_repo:
        if ns.import_path or ns.analyze_path:
            raise ValueError(
                'Multiple actions are forbidden.')

    if ns.apply:
        if not ns.recheck_repo:
            raise ValueError(
                '--apply requires --recheck')



if __name__ == "__main__":
    main()