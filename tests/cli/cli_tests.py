import os
import tempfile
import unittest
from glob import glob

from click.testing import CliRunner

from seedpod_ground_risk.cli import spgr


def test_file_exists(gpath):
    files = glob(gpath)
    if len(files) == 0:
        return False
    return True


class CLITestCase(unittest.TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.tmp_path = tempfile.mkdtemp().replace('\\', '/')
        self.runner = CliRunner()

        os.chdir(
            os.sep.join((
                os.path.dirname(os.path.realpath(__file__)),
                '..', '..'))
        )

        self.bounds_args = ' 50.8 51.0 -1.5 -1.3 '
        self.path_args = f' --output-path {self.tmp_path} '

    def test_map_pop_density(self):
        res = self.runner.invoke(spgr.pop_density, self.bounds_args + self.path_args)
        if res.exit_code != 0:
            print(res.exception)
            print(res.exc_info)
        self.assertEqual(res.exit_code, 0)
        self.assertTrue(test_file_exists(os.path.join(self.tmp_path, 'pop_density*')))

    def test_map_strike(self):
        res = self.runner.invoke(spgr.strike, self.bounds_args + self.path_args)
        if res.exit_code != 0:
            print(res.exception)
            print(res.exc_info)
        self.assertEqual(res.exit_code, 0)
        self.assertTrue(test_file_exists(os.path.join(self.tmp_path, 'strike*')))

    def test_map_fatality(self):
        res = self.runner.invoke(spgr.fatality, self.bounds_args + self.path_args)
        if res.exit_code != 0:
            print(res.exception)
            print(res.exc_info)
        self.assertEqual(res.exit_code, 0)
        self.assertTrue(test_file_exists(os.path.join(self.tmp_path, 'fatality*')))

    def test_path_make(self):
        path_args = ' 50.72 -1.48 50.88 -1.32 '

        res = self.runner.invoke(spgr.make, self.bounds_args + path_args + self.path_args)
        if res.exit_code != 0:
            print(res.exception)
            print(res.exc_info)
        self.assertEqual(res.exit_code, 0)
        self.assertTrue(test_file_exists(os.path.join(self.tmp_path, 'path*')))


if __name__ == '__main__':
    unittest.main()
