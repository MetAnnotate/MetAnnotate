import unittest
import subprocess
import glob


class TestEndToEnd(unittest.TestCase):

    # Unit test for validating test outputs from install to test script
    def test_endtoend(self):
        generated_fa_files = []

        # Fetch the generated fa files and verify that they match reference files
        for filename in glob.glob("../test_output/*.fa"):
            if filename.__contains__("msa") or filename.__contains__("refseq"):
                generated_fa_files.append(open(filename, 'r'))

        reference_fa_files = [open("test_constants/rpoB_0_msa_0.fa", 'r'),
                              open("test_constants/rpoB_0_refseq_msa_1.fa", 'r')]

        # compare the two FA files with reference
        if len(generated_fa_files) > 0:

            for i in range(0, 2):
                print 'Comparing reference file: ' + reference_fa_files[i].name
                temp_string_reference = ''
                temp_string_generated = ''

                for line in reference_fa_files[i]:
                    temp_string_reference = temp_string_reference.rstrip('\r\n') + line

                for line in generated_fa_files[i]:
                    temp_string_generated = temp_string_generated.rstrip('\r\n') + line

                # Get the first 100 chars of each string to improve consistency
                temp_string_reference = temp_string_reference[:100]
                temp_string_generated = temp_string_generated[:100]
                self.assertEqual(temp_string_reference, temp_string_generated)
        else:
            print("Please run test_metannotate.sh and verify that it works before running nosetests.")


if __name__ == '__main__':
    unittest.main()
