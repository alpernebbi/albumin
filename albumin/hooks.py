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


def pre_commit_hook():
    pass


def pre_commit_annex_hook():
    pass


def prepare_commit_msg_hook(editmsg, commit_type=None, commit_sha=None):
    pass


def commit_msg_hook(editmsg):
    pass


def post_commit_hook():
    pass


git_hooks = {
    'pre-commit': pre_commit_hook,
    'pre-commit-annex': pre_commit_annex_hook,
    'prepare-commit-msg': prepare_commit_msg_hook,
    'commit-msg': commit_msg_hook,
    'post-commit': post_commit_hook,
}
