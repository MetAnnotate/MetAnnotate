from modules import hash
import unittest
import subprocess
import os
import sys


class testEndToEnd(unittest.TestCase):

    def test_endtoend(self):
        subprocess.call("bash endtoend.sh", shell=True)

if __name__ == '__main__':
    unittest.main()
