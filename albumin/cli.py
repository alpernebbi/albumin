#!/usr/bin/env python3
import argparse
import albumin.core


def main():
    parser = argument_parser()
    namespace = parser.parse_args()
    kwargs = vars(namespace)

    if kwargs['import_path']:
        albumin.core.import_(**kwargs)
    elif kwargs['analyze_path']:
        albumin.core.analyze(**kwargs)


def argument_parser():
    parser = argparse.ArgumentParser(
        description="Manage photographs using a git-annex repository.")

    parser.add_argument(
        'repo_path',
        help="path of the git-annex repository",
        metavar='repo-path')

    actions = parser.add_mutually_exclusive_group()

    actions.add_argument(
        '--import',
        dest="import_path",
        help="import pictures from the given path",
        metavar="path")

    actions.add_argument(
        '--analyze',
        dest="analyze_path",
        help="analyze pictures in the given path",
        metavar="path")

    return parser


if __name__ == "__main__":
    main()