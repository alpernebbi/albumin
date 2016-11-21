#!/usr/bin/env python3
import argparse
import pytz

import albumin.core
from albumin.repo import AlbuminRepo


def main(*args):
    parser = argument_parser()
    ns = parser.parse_args(*args)
    validate_namespace(ns)

    if ns.interactive:
        interactive(ns.repo, parser)
    else:
        take_action(ns)


def take_action(ns):
    if ns.import_path:
        albumin.core.import_(ns.repo,
                             ns.import_path,
                             timezone=ns.timezone,
                             tags=ns.tags)
    elif ns.analyze_path:
        albumin.core.analyze(ns.analyze_path,
                             repo=ns.repo,
                             timezone=ns.timezone)


def interactive(repo, parser):
    while True:
        print('alb >>', end=' ')
        try:
            user_cmd = input()
        except EOFError:
            return
        if user_cmd == 'exit':
            return
        ns = parser.parse_args(user_cmd.split())
        ns.repo = repo
        validate_namespace(ns)
        take_action(ns)


def argument_parser():
    parser = argparse.ArgumentParser(
        description="Manage photographs using a git-annex repository.",
        usage='%(prog)s [repo-path] [action [option ...]]',
        add_help=False)

    positional = parser.add_argument_group('Positional arguments')

    positional.add_argument(
        'repo',
        metavar='repo_path',
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
        '--interactive',
        dest='interactive',
        action='store_true',
        help="use albumin as an interactive tool")

    options = parser.add_argument_group('Options')

    options.add_argument(
        '--timezone',
        dest='timezone',
        action='store',
        metavar='tz',
        help="assume pictures have dates in given timezone")

    options.add_argument(
        '--tags',
        dest='tags',
        action='store',
        metavar='x=y',
        nargs='+',
        help="add aditional tags to all imported files")

    return parser


def validate_namespace(ns):
    if ns.repo and not isinstance(ns.repo, AlbuminRepo):
        ns.repo = AlbuminRepo(ns.repo)

    if ns.import_path:
        if not ns.repo:
            raise ValueError(
                'Repository required for --import.')
        if ns.analyze_path or ns.interactive:
            raise ValueError(
                'Multiple actions are forbidden.')

    if ns.analyze_path:
        if ns.import_path or ns.interactive:
            raise ValueError(
                'Multiple actions are forbidden.')

    if ns.interactive:
        if not ns.repo:
            raise ValueError(
                '--interactive requires a repository')
        if ns.import_path or ns.analyze_path:
            raise ValueError(
                'Multiple actions are forbidden.')

    if ns.timezone:
        if not (ns.import_path or ns.analyze_path):
            raise ValueError(
                '--timezone requires either --import or --analyze')
        if ns.timezone not in pytz.all_timezones:
            raise ValueError(
                'Invalid timezone {}'.format(ns.timezone))
        ns.timezone = pytz.timezone(ns.timezone)

    if ns.tags:
        ns.tags = {x[0]: x[1] for x in (t.split('=') for t in ns.tags)}
        if not ns.import_path:
            raise ValueError(
                '--tags requires --import')
        forbidden_tags = ['datetime', 'datetime-method',
                          'year', 'month', 'day']
        for tag in ns.tags:
            if tag in forbidden_tags or 'lastchanged' in tag:
                raise ValueError(
                    'The following tag is forbidden: {}'.format(tag))


if __name__ == "__main__":
    main()
