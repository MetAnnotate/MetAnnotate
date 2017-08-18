#!/usr/bin/env python

"""
Created by: Metannotate

Description: A simple unittest for testing hash.py module

Requirements:
"""

# Imports:
from modules import hash
import unittest


class HashTesting(unittest.TestCase):

    def test_hash(self):
        """
        Description: Method that tests the methods 'hexhash()' and 'md5hash()' from module hash
        
        :param self: Reference to the HashTesting class
        :return:

        """
        self.assertEqual(hash.hexhash("This is a test string for hexhash"), "46e7d02b9a0d5339")
        self.assertEqual(hash.md5hash("test_constants/test_text_file.txt"), "f5c85408e67ef9a90f3e416863ba84de")

if __name__ == '__main__':
    unittest.main()
