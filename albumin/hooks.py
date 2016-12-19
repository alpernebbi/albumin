# Albumin Git Hooks
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

import os
import pygit2
import pytz
from datetime import datetime

from albumin.repo import AlbuminRepo
from albumin.imdate import analyze_date


def pre_commit_hook():
    repo = current_repo()
    new_files = repo.new_files()

    try:
        timezone = get_timezone(repo)
        print('Timezone: {}'.format(timezone))
    except pytz.exceptions.UnknownTimeZoneError as err:
        print("Invalid time zone: {}".format(err))
        return 1
    except KeyError:
        print("Please set albumin.timezone:")
        print("    $ git -c albumin.timezone=UTC commit ...")
        return 2

    file_data, remaining = analyze_date(*map(repo.abs_path, new_files))

    for imdate in file_data.values():
        imdate.timezone = timezone

    if remaining:
        print("No information about: ")
        for file in sorted(remaining):
            print('    {}'.format(file))
        return 3

    repo.arrange_by_imdates(file_data)
    repo.annex.pre_commit()


def pre_commit_annex_hook():
    pass


def prepare_commit_msg_hook(editmsg, commit_type=None, commit_sha=None):
    pass


def commit_msg_hook(editmsg):
    pass


def post_commit_hook():
    pass


def current_repo():
    return AlbuminRepo(os.getcwd(), create=False)


def git_config_overrides():
    try:
        git_config_parameters = os.getenv('GIT_CONFIG_PARAMETERS')
        git_config_lines = git_config_parameters[1:-1].split('\' \'')
        return dict(config.split('=') for config in git_config_lines)
    except:
        return {}


def get_timezone(repo=None):
    tz = git_config_overrides().get('albumin.timezone', '')
    if repo and not tz:
        tz = repo.config['albumin.timezone']
        print('Using default timezone.')
    return pytz.timezone(tz)


git_hooks = {
    'pre-commit': pre_commit_hook,
    'pre-commit-annex': pre_commit_annex_hook,
    'prepare-commit-msg': prepare_commit_msg_hook,
    'commit-msg': commit_msg_hook,
    'post-commit': post_commit_hook,
}