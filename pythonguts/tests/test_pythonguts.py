from pathlib import Path
import shutil
import subprocess, os, filecmp
import unittest
import sys


class test_basics(unittest.TestCase):
    this_dir = os.path.dirname(__file__)
    data_dir = os.path.join(this_dir, 'data')
    tmp_dir = os.path.join(this_dir, 'tmp')
    src = os.path.join(tmp_dir, 'src.py')
    dest = os.path.join(tmp_dir, 'dest.py')
    srcin = os.path.join(data_dir, 'src.py.in')
    destin = os.path.join(data_dir, 'dest.py.in')

    def setUp(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        Path(self.tmp_dir).mkdir(parents=True, exist_ok=True)
        shutil.copy(self.srcin, self.src)
        shutil.copy(self.destin, self.dest)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_basics(self):
        os.environ["PATH"] += os.pathsep + os.path.dirname(sys.executable)
        guts_env = os.environ.copy()
        guts_env["PATH"] += os.pathsep + os.path.dirname(sys.executable)
        subprocess.run(['editpy', '--src-file', self.src, '--dest-file', self.dest], env=guts_env)

        with open(self.dest) as f:
            with open(self.destin) as fin:
                self.assertTrue(f != fin)