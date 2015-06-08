#!/bin/bash

echo "Installing UI version of metAnnotate...\n\nNote that you should have already run base_installation.sh. Also note that this script requires sudo permissions.\n\n"

echo "Installing packages and python modules.\n"
apt-get install python-mysqldb
apt-get install rabbitmq-server
apt-get install sqlite3
pip install bottle
pip install beaker
pip install ete2
pip install paramiko
pip install biopython
pip install celery

echo "Downloading and indexing HMMs.\n"
cd precompute/
wget "ftp://ftp.jcvi.org/pub/data/TIGRFAMs/GEN_PROP/PROP_DEF_WITHOUT_DESCRIPTION_FIELD.TABLE"
wget "ftp://ftp.jcvi.org/pub/data/TIGRFAMs/GEN_PROP/PROP_GO_LINK.TABLE"
wget "ftp://ftp.jcvi.org/pub/data/TIGRFAMs/GEN_PROP/PROP_STEP.TABLE"
wget "ftp://ftp.jcvi.org/pub/data/TIGRFAMs/GEN_PROP/STEP_EV_LINK.TABLE"
wget "ftp://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/Pfam-A.hmm.gz"
gunzip Pfam-A.hmm.gz
wget "ftp://ftp.jcvi.org/pub/data/TIGRFAMs/TIGRFAMs_*_HMM.tar.gz"
tar -xzf TIGRFAMs_* -C ../data/hmms/
python make_hmms_json.py
cd ..

rm -f precompute/TIGRFAMs_*.tar.gz

echo "Done installing the UI version of metAnnotate.\n\nIMPORTANT: The UI version is not yet ready for running, as you will still need to configure the metagenome directories files. You need to create 2 files:\n\nmetagenome_directories_root.txt\nmetagenome_directories.txt\n\nSee metagenome_directories_sample.txt and metagenome_directories_root_sample.txt for reference. These files need to be placed in the main metannotate direcoty (current directory). metagenome_directories_root.txt contains the root path for all metagenome directories that will be read by the program. metagenome_directories.txt lists all the directories in that root directory that should be read as metagenome directories (in the case that you have other directories in the root directory that shouldn't be interpreted as metagenome directories)."


