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
    albumin analyze [<path>] [--repo=<repo>] [--timezone=<tz>]
    albumin import <path> [--repo=<repo>] [--timezone=<tz>] [--tag=<tag>:<value>]...

Actions:
    analyze                 Analyze files in the repo's staging area
    analyze <path>          Analyze the files at <path>
    import <path>           Import files from <path>

Options:
    --repo=<repo>           Git-annex repository to use. [default: .]
    --timezone=<tz>         Timezone to assume pictures are in.
    --tag=<tag>:<value>     Tags to add to all imported files.

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
        sys.exit(hook(args))

    args = docopt(__doc__, version=version)

    if args.get('--repo'):
        try:
            args['--repo'] = AlbuminRepo(args['--repo'])
        except ValueError:
            if args.get('import'):
                raise
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

    if args.get('analyze') and args.get('--repo'):
        albumin.core.repo_analyze(
            repo=args['--repo'],
            path=args['<path>'],
        )

    elif args.get('analyze'):
        albumin.core.imdate_analyze(
            path=args['<path>'],
            timezone=args['--timezone']
        )

    elif args.get('import'):
        albumin.core.import_(
            repo=args['--repo'],
            path=args['<path>'],
            **args['--tag']
        )

if __name__ == "__main__":
    main()
