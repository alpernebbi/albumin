#!/usr/bin/env python3

import argparse
import os

from albumin.gitrepo import GitAnnexRepo
from albumin.utils import sequenced_folder_name


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
    repo = GitAnnexRepo(repo_path)
    current_branch = repo.branches[0]

    repo.checkout('albumin-imports')
    repo.annex.import_(import_path)
    import_name = os.path.basename(import_path)
    batch_name = sequenced_folder_name(repo_path)
    repo.move(import_name, batch_name)
    repo.commit("Import batch {} ({})".format(batch_name, import_name))

    if current_branch:
        repo.checkout(current_branch)


if __name__ == "__main__":
    main()
