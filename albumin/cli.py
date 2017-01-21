#!/usr/bin/env python3

# Albumin
# Copyright (C) 2016 Alper Nebi Yasak
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
Albumin. Manages photographs using a git-annex repository.

Usage:
    albumin init [-r=<repo>]
    albumin uninit [-r=<repo>]
    albumin analyze [<path>] [-s] [-m] [-r=<repo>] [-T=<tz>]
    albumin import <path> [-m] [-r=<repo>] [-T=<tz>] [-t=<tag>:<value>]...
    albumin fix [<path>] [-r=<repo>]
    albumin apply <path> [-r=<repo>] [-t=<tag>:<value>]...

Actions:
    init                    Initialize the repo and set up git hooks
    uninit                  Remove albumin git hooks in the repo
    analyze                 Analyze files in the repo's staging area
    analyze <path>          Analyze the files at <path>
    import <path>           Import files from <path>
    fix                     Fix the filenames of all images
    fix <path>              Fix the filenames of images in <path>
    apply <path>            Apply the analysis report to metadata

Options:
    -r, --repo=<repo>         Git-annex repository to use. [default: .]
    -T, --timezone=<tz>       Timezone to assume pictures are in.
    -t, --tag=<tag>:<value>   Tags to add to all imported files.
    -s, --short               Print analysis report in the short format
    -m, --mtime               Use file modify time as a valid image date

"""

import os
import sys
import pytz
from docopt import docopt

import albumin.core
from albumin.repo import AlbuminRepo
from albumin.hooks import git_hooks


def main():
    name = os.path.basename(sys.argv[0])
    version = '0.1.0'

    if name in git_hooks:
        hook = git_hooks[name]
        args = docopt(hook.__doc__, version=version)
        retval = hook(args)
        if retval:
            print('Aborting commit.')
        sys.exit(retval)

    args = docopt(__doc__, version=version)

    if args.get('--repo'):
        try:
            args['--repo'] = AlbuminRepo(args['--repo'])
        except ValueError:
            repo_cmds = ['import', 'fix', 'apply']
            if any(map(args.__getitem__, repo_cmds)):
                raise
            elif args.get('init'):
                args['--repo'] = AlbuminRepo(
                    args['--repo'], create=True
                )
            else:
                args['--repo'] = None

    if args.get('--timezone'):
        args['--timezone'] = pytz.timezone(args['--timezone'])
        if args.get('--repo'):
            args['--repo'].timezone = args['--timezone']

    if args.get('--tag'):
        args['--tag'] = dict(t.split(':') for t in args['--tag'])
        for tag, value in args['--tag'].items():
            if tag in args['--repo'].annex.internal_tags:
                raise ValueError(tag)
            if tag.endswith('lastchanged'):
                raise ValueError(tag)
    else:
        args['--tag'] = {}

    if args.get('analyze') and args.get('--repo'):
        albumin.core.repo_analyze(
            repo=args['--repo'],
            path=args['<path>'],
            short=args['--short'],
            mtime=args['--mtime'],
        )

    elif args.get('init'):
        albumin.core.init(
            repo=args['--repo'],
            exec_path=sys.argv[0]
        )

    elif args.get('uninit'):
        albumin.core.uninit(
            repo=args['--repo'],
            exec_path=sys.argv[0]
        )

    elif args.get('analyze'):
        albumin.core.imdate_analyze(
            path=args['<path>'],
            short=args['--short'],
            timezone=args['--timezone'],
            mtime=args['--mtime'],
        )

    elif args.get('import'):
        albumin.core.import_(
            repo=args['--repo'],
            path=args['<path>'],
            mtime=args['--mtime'],
            **args['--tag'],
        )

    elif args.get('fix'):
        albumin.core.fix(
            repo=args['--repo'],
            path=args['<path>'],
        )

    elif args.get('apply'):
        albumin.core.apply(
            repo=args['--repo'],
            path=args['<path>'],
            **args['--tag'],
        )

if __name__ == "__main__":
    main()
