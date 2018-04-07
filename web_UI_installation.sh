#!/bin/bash
set -euxo pipefail

echo "Installing UI version of metAnnotate...\n\nNote that you should have already run base_installation.sh and refseq_installation.sh. Also note that this script requires sudo permissions.\n\n"

PATH="${PATH}:${HOME}/.local/bin"
softwareDir="${HOME}/.local/bin"

echo "Installing packages and python modules.\n"

echo "preparing rabbitmq-server installation"
echo 'deb http://www.rabbitmq.com/debian/ stable main' | sudo tee /etc/apt/sources.list.d/rabbitmq.list
wget -O- https://www.rabbitmq.com/rabbitmq-release-signing-key.asc | sudo apt-key add -
sudo apt-get update
echo "preparation complete"

echo "begin installation"
sudo apt-get install -y python-mysqldb rabbitmq-server libssl-dev libffi-dev sqlite3

sudo ${softwareDir}/pip install bottle --ignore-installed
sudo ${softwareDir}/pip install beaker --ignore-installed
sudo ${softwareDir}/pip install ete2 --ignore-installed
sudo ${softwareDir}/pip install paramiko --ignore-installed
sudo ${softwareDir}/pip install biopython --ignore-installed
sudo ${softwareDir}/pip install celery --ignore-installed
echo "installed all dependencies and python modules"

echo "Downloading and indexing HMMs.\n"
cd precompute/
wget "ftp://ftp.jcvi.org/pub/data/TIGRFAMs/GEN_PROP/PROP_DEF_WITHOUT_DESCRIPTION_FIELD.TABLE"
wget "ftp://ftp.jcvi.org/pub/data/TIGRFAMs/GEN_PROP/PROP_GO_LINK.TABLE"
wget "ftp://ftp.jcvi.org/pub/data/TIGRFAMs/GEN_PROP/PROP_STEP.TABLE"
wget "ftp://ftp.jcvi.org/pub/data/TIGRFAMs/GEN_PROP/STEP_EV_LINK.TABLE"
wget "ftp://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/Pfam-A.hmm.gz"
gunzip Pfam-A.hmm.gz
python pfam_splitter.py
wget "ftp://ftp.jcvi.org/pub/data/TIGRFAMs/TIGRFAMs_*_HMM.tar.gz"
tar -xzf TIGRFAMs_* -C ../data/hmms/
python make_hmms_json.py
cd ..

rm -f precompute/TIGRFAMs_*.tar.gz
rm -f precompute/Pfam-A.hmm

echo -e "Done installing the UI version of metAnnotate.\n"
echo -e "\nIMPORTANT: The UI version is not yet ready for running, as you will still need to configure the metagenome directories files. You need to create 2 files:\n\nmetagenome_directories_root.txt\nmetagenome_directories.txt\n\nSee metagenome_directories_sample.txt and metagenome_directories_root_sample.txt for reference. These files need to be placed in the main metannotate direcoty (current directory). metagenome_directories_root.txt contains the root path for all metagenome directories that will be read by the program. metagenome_directories.txt lists all the directories in that root directory that should be read as metagenome directories (in the case that you have other directories in the root directory that shouldn't be interpreted as metagenome directories)."

