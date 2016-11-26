# Albumin Core Tests
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

from unittest import TestCase
from tests.utils import with_repo
from tests.utils import with_folder

from albumin.core import import_


class TestAlbuminCore(TestCase):
    @with_repo(annex=True)
    @with_folder('data-tars/three-nested.tar.gz')
    def test_import_basics(self, repo, temp_folder):
        self.skipTest('Invalid files for importing. \n')
        current_branch = repo.branches[0]
        import_(repo.path, temp_folder)
        assert repo.branches[0] == current_branch

        repo.checkout('albumin-imports')
        assert repo.tree_hash == \
               '3cf88503d354f1bd291d4d30cc12a023896dff09'
