#!/usr/bin/env python3

import argparse


def argument_parser():
    parser = argparse.ArgumentParser(
        description="Manage photographs using a git-annex repository.")

    parser.add_argument(
        'repo_path',
        help="path of the git-annex repository",
        metavar='repo-path')

    parser.add_argument(
        '--import',
        dest="import_path",
        help="import pictures from the given path",
        metavar="path")

    return parser


def main():
    parser = argument_parser()
    namespace = parser.parse_args()
    kwargs = vars(namespace)

    if kwargs['import_path']:
        import_(**kwargs)


def import_(repo_path, import_path, **kwargs):
    raise NotImplementedError


if __name__ == "__main__":
    main()
