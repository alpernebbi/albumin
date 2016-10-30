#!/usr/bin/env python3
import argparse
import collections
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
        action=ChangeRequirementsAction('store'),
        free=['repo_path'],
        help="analyze pictures in the given path",
        metavar="path")

    return parser


def ChangeRequirementsAction(base_action=None):
    action_classes = {
        None: argparse._StoreAction,
        'store': argparse._StoreAction,
        'store_const': argparse._StoreConstAction,
        'store_true': argparse._StoreTrueAction,
        'store_false': argparse._StoreFalseAction,
        'append': argparse._AppendAction,
        'append_const': argparse._AppendConstAction,
        'count': argparse._CountAction,
        'help': argparse._HelpAction,
        'version': argparse._VersionAction,
        'parsers': argparse._SubParsersAction
    }

    class CustomAction(action_classes[base_action]):
        def __init__(self, *args, require=None, free=None, **kwargs):
            super().__init__(*args, **kwargs)
            if not isinstance(require, collections.Iterable):
                require = [require]
            if not isinstance(free, collections.Iterable):
                free = [free]
            self.require = require
            self.free = free

        def __call__(self, parser, *args, **kwargs):
            for action in parser._actions:
                if action.dest in self.require:
                    action.required = True
                if action.dest in self.free:
                    action.required = False
            try:
                return super().__call__(parser, *args, **kwargs)
            except NotImplementedError:
                pass

    return CustomAction

if __name__ == "__main__":
    main()