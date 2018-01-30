#!/bin/bash

# Robust bash header (Buffalo, 2015):
set -e
set -u
set -o pipefail

echo "Installing RefSeq database. Could take some time to download."
metAnnotateDir="`pwd`"

if [ ! `which wget` ]; then
    sudo apt-get -y install wget
fi

cd ${metAnnotateDir}/data
if [ ! -e "Refseq.fa" ] || [ ! -e "Refseq.fa.ssi" ]; then
    echo "Downloading RefSeq database; could take a few hours if connection is slow"
    # Note: the old code that was here for downloading RefSeq directly from NCBI (instead of from Zenodo) implied that
    # multiple files were downloaded from NCBI and then combined during a preprocessing step. Watch for this when
    # updating this code to pull directly from NCBI again instead of from Zenodo; some modifications may be needed.
    wget "https://zenodo.org/record/1098450/files/metannotate_refseq_db_w_gi_2017_03_01.fa.bz2"
    pbzip2 -d -c metannotate_refseq_db_w_gi_2017_03_01.fa.bz2 > Refseq.fa
    echo "Preprocessing Refseq.fa to removing uncommon amino acids"
    perl ../scripts/cleanDatabase.pl Refseq.fa > list_to_remove.txt
    perl ../scripts/removeFromFasta.pl list_to_remove.txt Refseq.fa > Refseq.fixed.fa
    rm list_to_remove.txt
    rm Refseq.fa
    mv Refseq.fixed.fa Refseq.fa
    echo "Preprocessing completes"
    rm metannotate_refseq_db_w_gi_2017_03_01.fa.bz2
    esl-sfetch --index Refseq.fa
fi

echo "Download successful."
