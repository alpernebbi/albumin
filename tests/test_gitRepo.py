from unittest import TestCase
import tempfile

from gitrepo import GitRepo


class TestGitRepo(TestCase):
    def test_git(self):
        with tempfile.TemporaryDirectory() as repo_path:
            repo = GitRepo(repo_path)
            print(repo._git('init'))
            print(repo._git('status'))
