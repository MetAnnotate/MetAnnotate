#!/usr/bin/env bash
set -euxo pipefail

# ======================================================================================================================
# Created by: Metannotate Team (2017)
#
# Description: A shell script that runs a sample test of Metannotate and compares the generated
#              output files to verify proper end-to-end functionality of the program.
#
# Requirements: - A full CLI installation of Metannotate
# ======================================================================================================================

# TODO - add try-catch statement to report if running metannotate itself fails
echo "Running Metannotate..."
python run_metannotate.py --orf_files=data/MetagenomeTest.fa --hmm_files=data/hmms/RPOB.HMM --reference_database=data/ReferenceTest.fa --output_dir=test_output --tmp_dir=test_tmp --run_mode=both

echo "Verifying outputs..."

cd testing/test_constants

# Get reference hash file checksums
FIRST_HASH=$(md5sum rpoB_0_msa_0.fa | cut -d ' ' -f 1)
SECOND_HASH=$(md5sum rpoB_0_refseq_msa_1.fa | cut -d ' ' -f 1)

cd ../..

# Store generated test output hashes in array
declare -a REGENERATED_FILE_HASHES

for entry in $(ls test_output); do
    # Checks if entry is the one we are looking to compare
    if [[ ${entry} == *"0_msa"* && ${entry} == *".fa"* ]]; then
        cd test_output
        REGENERATED_FILE_HASHES[0]=$(md5sum ${entry} | cut -d ' ' -f 1)
        cd ..
    fi

    # Checks if entry is the one we are looking to compare
    if [[ ${entry} == *"refseq"* && ${entry} == *".fa"* ]]; then
        cd test_output
        REGENERATED_FILE_HASHES[1]=$(md5sum ${entry} | cut -d ' ' -f 1)
        cd ..
    fi
done

# If the hashes match, pass the test.
if [[ ${REGENERATED_FILE_HASHES[0]} == ${FIRST_HASH} && ${REGENERATED_FILE_HASHES[1]} == ${SECOND_HASH} ]]; then
    echo "Hash matches! Test passes."
    exit 0
else
    echo "Hash mismatch! Test fails."
    exit 1
fi
