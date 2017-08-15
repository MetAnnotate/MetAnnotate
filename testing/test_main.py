import unittest, hash


class FullInstallTest(unittest.TestCase):

    def test_dummy(self):
        self.assertEqual('hello', 'hello')

    def test_hash(self):
        self.assertEqual(hash.hexhash("This is a test string for hexhash"), "46e7d02b9a0d5339")
        self.assertEqual(hash.md5hash("test_constants/test_text_file.txt"), "f5c85408e67ef9a90f3e416863ba84de")


if __name__ == '__main__':
    unittest.main()
