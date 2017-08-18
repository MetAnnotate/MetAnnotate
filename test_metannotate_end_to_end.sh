#!/usr/bin/env bash#!/usr/bin/env bash

"""
Created by: Metannotate Team (2017)

Description: A shell script that runs a sample test of Metannotate and compares the generated
             output files to verify proper end-to-end functionality of the program.

Requirements: - The following packages:
                    - build-essential
                    - python-dev
                    - curl
                    - file
                    - git
                    - python-setuptools
                    - ruby
              - Base installation (sudo -H bash base_installation.sh) of Metannotate

"""

python run_metannotate.py --orf_files=data/MetagenomeTest.fa --hmm_files=data/hmms/RPOB.HMM --reference_database=data/ReferenceTest.fa --output_dir=test_output --tmp_dir=test_tmp --run_mode=both

echo "Verifying outputs..."

cd testing/test_constants

# Get reference hash file checksums

FIRST_HASH=$(md5sum rpoB_0_msa_0.fa | awk '{ print $1 }')

SECOND_HASH=$(md5sum rpoB_0_refseq_msa_1.fa | awk '{ print $1 }')


cd ..
cd ..

# Store generated test output hashes in array

declare -a GENERATED_FILES

for entry in $(ls test_output); do
    if [[ ${entry} == *"0_msa"* && ${entry} == *".fa"* ]]; then
        cd test_output
        GENERATED_FILES[0]=$(md5sum ${entry} | awk '{ print $1 }')
        cd ..

    fi
    if [[ ${entry} == *"refseq"* && ${entry} == *".fa"* ]]; then
        cd test_output
        GENERATED_FILES[1]=$(md5sum ${entry} | awk '{ print $1 }')
        cd ..
    fi
done

# Compare hashes and if there is a match exit 0 else exit 1

if [[ ${GENERATED_FILES[0]} == ${FIRST_HASH} && ${GENERATED_FILES[1]} == ${SECOND_HASH} ]]; then
    echo ${SEPARATOR_TWO}
    echo "Hash matches! Exit code: 0"
    exit 0
else
    echo ${SEPARATOR_TWO}
    echo "Hash mismatch! Exit code: 1"
    exit 1
fi