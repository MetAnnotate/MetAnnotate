#!/usr/bin/env bash

# ======================================================================================================================
# Created by: Metannotate Team (2017)
#
# Description: A shell script that runs a sample test of Metannotate and compares the generated
#              output files to verify proper end-to-end functionality of the program.
#
# Requirements: - A full CLI installation of Metannotate
# ======================================================================================================================

echo "Running Metannotate..."
python run_metannotate.py --orf_files=data/MetagenomeTest.fa --hmm_files=data/hmms/RPOB.HMM --reference_database=data/ReferenceTest.fa --output_dir=test_output --tmp_dir=test_tmp --run_mode=both

echo "Verifying outputs..."

EXIT_CODE=0
ROOT_PATH=$(pwd)

## Check that the number of files in --output_dir is correct
# TODO: replace this test with individual tests for each expected file
NUM_OUTPUT_FILES=$(ls ${ROOT_PATH}/test_output | wc -l | sed 's/ //g')
CORRECT_NUM_FILES=13
if [[ ${NUM_OUTPUT_FILES} -eq ${CORRECT_NUM_FILES} ]]; then
    echo "Correct number of files in output_dir ("${CORRECT_NUM_FILES}")"
else
    echo "Unexpected number of files in output_dir. Expected: "${CORRECT_NUM_FILES}"; Produced: "${NUM_OUTPUT_FILES}
    EXIT_CODE=1
fi

## Check hashes
# Get reference hash file checksums
declare -a REFERENCE_FILE_HASHES
cd ${ROOT_PATH}/testing/test_constants
REFERENCE_FILE_HASHES[0]=$(md5sum rpoB_0_msa_0.fa | cut -d ' ' -f 1)
REFERENCE_FILE_HASHES[1]=$(md5sum rpoB_0_refseq_msa_1.fa | cut -d ' ' -f 1)
# only first 14 columns of annotations table are consistent between runs
REFERENCE_FILE_HASHES[2]=$(cut -f 1-14 rpoB_0_MetagenomeTest_0_annotations.tsv | md5sum | cut -d ' ' -f 1)

# Store generated test output hashes in array
# Keys in REFERENCE_FILE_HASHES should correspond to same key in REGENERATED_FILE_HASHES
declare -a REGENERATED_FILE_HASHES
declare -a CHECKED_FILES
cd ${ROOT_PATH}/test_output
for entry in $(ls); do
    # Checks if entry is the query msa fasta
    if [[ ${entry} == rpoB_0_msa*fa ]]; then
        REGENERATED_FILE_HASHES[0]=$(md5sum ${entry} | cut -d ' ' -f 1)
        CHECKED_FILES[0]=${entry}
    fi

    # Checks if entry is the refseq msa fasta
    if [[ ${entry} == rpoB_0_refseq_msa*fa ]]; then
        REGENERATED_FILE_HASHES[1]=$(md5sum ${entry} | cut -d ' ' -f 1)
        CHECKED_FILES[1]=${entry}
    fi

    # Checks if entry is the annotations table
    # Only the first 14 columns are consistent between metannotate runs
    if [[ ${entry} == rpoB_0_MetagenomeTest_0_annotations*tsv ]]; then
        REGENERATED_FILE_HASHES[2]=$(cut -f 1-14 ${entry} | md5sum | cut -d ' ' -f 1)
        CHECKED_FILES[1]=${entry}
    fi
done

# If the hashes match, pass the test
# Keys in REFERENCE_FILE_HASHES should correspond to same key in REGENERATED_FILE_HASHES
for entry_index in ${!CHECKED_FILES[@]}; do
    if [[ ${REFERENCE_FILE_HASHES[$entry_index]} == ${REGENERATED_FILE_HASHES[$entry_index]} ]]; then
        echo ${CHECKED_FILES[$entry_index]}" passed the hash check."
    else
        echo ${CHECKED_FILES[$entry_index]}" failed the hash check."
        EXIT_CODE=1
    fi
done

exit ${EXIT_CODE}