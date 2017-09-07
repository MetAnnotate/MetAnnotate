#!/usr/bin/env python

"""
Created by: Metannotate Team (2017)

Description: A simple unittest for testing the hash.py module
"""

# Imports:
from modules import hash
import unittest


class HashTesting(unittest.TestCase):
    """
    Description: A unit testing class for testing the hash.py module. Tests the functions 'hexhash' and 'md5hash'.
    Called by nosetests in circleci's config.yml.
    """

    def test_hash(self):
        """
        Description: Method that tests the methods 'hexhash()' and 'md5hash()' from module hash
        """
        self.assertEqual(hash.hexhash("This is a test string for hexhash"), "46e7d02b9a0d5339")
        self.assertEqual(hash.md5hash("test_constants/test_text_file.txt"), "f5c85408e67ef9a90f3e416863ba84de")

if __name__ == '__main__':
    unittest.main()
