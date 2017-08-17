import unittest
import hashlib
import glob


class testEndToEnd(unittest.TestCase):

    # Method that returns the md5 hash of a given file
    def generate_md5(filename):
        hash_md5 = hashlib.md5()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    # Unit test for validating test outputs from install to test script
    def test_endtoend(self):
        generated_hash = []

        # Fetch the generated fa files and verify that they match reference files
        for filename in glob.glob("../test_output/*.fa"):
            if filename.__contains__("msa") or filename.__contains__("refseq"):
                generated_hash.append(self.generate_md5(filename))

        reference_hash = [self.generate_md5("test_constants/rpoB_0_msa_0.fa"),
                          self.generate_md5("test_constants/rpoB_0_refseq_msa_1.fa")]

        # compare the two FA files with reference
        if len(generated_hash) > 0:
            for i in range(0, 2):
                self.assertEqual(generated_hash[0], reference_hash[0])
        else:
            print("Please run test_metannotate.sh and verify that it works before running nosetests.")


if __name__ == '__main__':
    unittest.main()
