#!/usr/bin/env python3

import argparse


def argument_parser():
    parser = argparse.ArgumentParser(
        description="Manage photographs using a git-annex repository.")

    parser.add_argument(
        'repo_path',
        help="path of the git-annex repository",
        metavar='repo-path')

    return parser


def main():
    parser = argument_parser()
    args = parser.parse_args()


if __name__ == "__main__":
    main()
