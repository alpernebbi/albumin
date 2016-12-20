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

import sys
import pytz
from docopt import docopt

import albumin.core
from albumin.repo import AlbuminRepo


def main():
    name = sys.argv[0]
    args = docopt(__doc__, version='0.1.0')

    if args.get('--repo'):
        try:
            args['--repo'] = AlbuminRepo(args['--repo'])
        except ValueError:
            if args.get('import'):
                raise
            args['--repo'] = None

    if args.get('--timezone'):
        args['--timezone'] = pytz.timezone(args['--timezone'])

    if args.get('--tag'):
        args['--tag'] = dict(t.split(':') for t in args['--tag'])

    if args['analyze']:
        albumin.core.analyze(
            analyze_path=args['<path>'],
            repo=args['--repo'],
            timezone=args['--timezone']
        )

    elif args['import']:
        albumin.core.import_(
            repo=args['--repo'],
            import_path=args['<path>'],
            timezone=args['--timezone'],
            tags=args['--tag']
        )

if __name__ == "__main__":
    main()
