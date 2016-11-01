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
    elif kwargs['recheck_repo']:
        albumin.core.recheck(**kwargs)


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
        action=MultiAction,
        actions=['store', ChangeRequirementsAction],
        free='repo_path',
        help="analyze pictures in the given path",
        metavar="path")

    actions.add_argument(
        '--recheck',
        dest="recheck_repo",
        action='store_true',
        help="recheck files in repo for new metadata")

    return parser


class MultiAction(argparse.Action):
    def __init__(self, *args, actions=None, **kwargs):
        custom_kwargs, default_kwargs = self.split_custom_args(kwargs)
        super().__init__(*args, **default_kwargs)
        self.custom_kwargs = custom_kwargs

        self.acts = []
        for action in actions:
            if isinstance(action, type):
                action_cls = action
            elif isinstance(action, str):
                action_cls = self.get_action_class(action)

            try:
                action_obj = action_cls(*args, **kwargs)
            except TypeError:
                action_obj = action_cls(*args, **default_kwargs)
            self.acts.append(action_obj)

    def __call__(self, *args, **kwargs):
        for act in self.acts:
            try:
                act.__call__(*args, **kwargs)
            except NotImplementedError:
                pass

    @staticmethod
    def get_action_class(action=None):
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
        return action_classes.get(action)

    @staticmethod
    def split_custom_args(kwargs):
        defaults = ['option_strings', 'dest', 'nargs', 'const',
                    'default', 'type', 'choices', 'required', 'help',
                    'metavar']
        split_args = ({}, {})
        for k, v in kwargs.items():
            split_args[k in defaults][k] = v
        return split_args

    def __repr__(self):
        defaults = super().__repr__()[:-1]
        customs = ', {}={{}}' * len(self.custom_kwargs)
        customs = customs.format(*self.custom_kwargs.keys())
        customs = customs.format(*self.custom_kwargs.values())
        actions = [type(x).__name__ for x in self.acts]
        actions = ', acts={!r})'.format(actions)
        return defaults + customs + actions


class ChangeRequirementsAction(argparse.Action):
    def __init__(self, *args, require=None, free=None, **kwargs):
        _, default_kwargs = MultiAction.split_custom_args(kwargs)
        super().__init__(*args, **default_kwargs)
        self.require = require if require else []
        self.free = free if free else []

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

    def __repr__(self):
        defaults = super().__repr__()[:-1]
        customs = 'require={!r}, free={!r}'
        customs = customs.format(self.require, self.free)
        return '{}, {})'.format(defaults, customs)


if __name__ == "__main__":
    main()