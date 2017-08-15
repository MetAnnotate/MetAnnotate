from modules import hash
import unittest
import subprocess
import os, os.path
import glob


class testEndToEnd(unittest.TestCase):

    def getFileContents(mFile):
        returnable = ''

        for line in mFile:
            returnable =  returnable + line

        return returnable

    def test_endtoend(self):
        subprocess.call("bash endtoend.sh", shell=True)
        generatedFaFiles = []
        for filename in glob.glob("../test_output/*.fa"):
            if filename.__contains__("msa") or filename.__contains__("refseq"):
                generatedFaFiles.append(open(filename, 'r'))

        referenceFaFiles = [open("test_constants/rpoB_0_msa_0.fa", 'r'),
                            open("test_constants/rpoB_0_refseq_msa_1.fa", 'r')]

        # To be replaced by generated fa files



        for i in range(0,2):
            print 'Comparing reference file: ' + referenceFaFiles[i].name
            tempStringReference = ''
            tempStringGenerated = ''
            for line in referenceFaFiles[i]:
                tempStringReference = tempStringReference + line
            for line in generatedFaFiles[i]:
                tempStringGenerated = tempStringGenerated + line
            self.assertEqual(tempStringReference, tempStringGenerated)



if __name__ == '__main__':
    unittest.main()
