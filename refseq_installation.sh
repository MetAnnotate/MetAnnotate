#!/bin/bash

# Robust bash header (Buffalo, 2015):
set -e
set -u
set -o pipefail

metAnnotateDir="`pwd`"

# Parse user inputs: get the download location if requested
if [ $# == 0 ]; then

    # If no arguments are provided, then assign the default download directory
    output_dir="${metAnnotateDir}/data"
    echo "Installing RefSeq database."
    echo "No user input provided. Will download to the default directory '${output_dir}'."

elif [ $# == 1 ]; then
    input=$1

    if [ $input == "-h" -o $input == "--help" ]; then
        # Provide help info and exit
        echo "${0}: Downloads and indexes RefSeq database for MetAnnotate."
        echo "Usage: ${0} [download_directory]"
        echo "MUST be run within the main MetAnnotate folder."
        echo "If no download_directory is specified, the script will download the database to the 'data' directory within the MetAnnotate folder."
        echo ""
        exit 1
    else
        # Get user-provided output directory
        output_dir=$input
        echo "Installing RefSeq database."
        echo "Downloading to the provided directory '${output_dir}'."
    fi

elif [ $# > 1 ]; then

    echo "ERROR: more than one argument was provided to the script. Try '-h'. Job terminating."
    exit 1

fi

if [ ! `which wget` ]; then
    sudo apt-get -y install wget
fi

cd ${output_dir}
if [ ! -e "Refseq.fa" ] || [ ! -e "Refseq.fa.ssi" ]; then
    echo "Downloading RefSeq database; could take a few hours if connection is slow"
    # Note: the old code that was here for downloading RefSeq directly from NCBI (instead of from Zenodo) implied that
    # multiple files were downloaded from NCBI and then combined during a preprocessing step. Watch for this when
    # updating this code to pull directly from NCBI again instead of from Zenodo; some modifications may be needed.
    wget "https://zenodo.org/record/1098450/files/metannotate_refseq_db_w_gi_2017_03_01.fa.bz2"
    pbzip2 -d -c metannotate_refseq_db_w_gi_2017_03_01.fa.bz2 > Refseq.fa
    echo "Preprocessing Refseq.fa to removing uncommon amino acids"
    perl ${metAnnotateDir}/scripts/cleanDatabase.pl Refseq.fa > list_to_remove.txt
    perl ${metAnnotateDir}/scripts/removeFromFasta.pl list_to_remove.txt Refseq.fa > Refseq.fixed.fa
    rm list_to_remove.txt
    rm Refseq.fa
    mv Refseq.fixed.fa Refseq.fa
    echo "Preprocessing completes"
    rm metannotate_refseq_db_w_gi_2017_03_01.fa.bz2
    esl-sfetch --index Refseq.fa
    echo "Download successful. Saved to ${output_dir}."
else
    echo "Found Refseq.fa and Refseq.fa.ssi in '${output_dir}'. RefSeq is already installed and indexed. Nothing to do."
fi
