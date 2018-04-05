#!/bin/bash

# Robust bash header (Buffalo, 2015):
set -e
set -u
set -o pipefail

echo "Installing commandline and web version of MetAnnotate, along with database"
echo "This is going to need root access and will take a while."
metAnnotateDir="`pwd`"

echo "installing all dependencies"
sudo apt-get install -y python-dev build-essential default-jre
echo "dependency installation complete, running main installation"

# Run setup scripts
bash ./base_installation.sh
bash ./web_UI_installation.sh
bash ./refseq_installation.sh

# Create example metagenome directory files for the web UI
cd ${metAnnotateDir}
mkdir -p "${HOME}/metagenome_files/sample"
echo "${HOME}/metagenome_files" > metagenome_directories_root.txt
echo "${HOME}/metagenome_files/sample" > metagenome_directories.txt

echo "===Testing newly installed MetAnnotate==="
bash testing/test_metannotate_end_to_end.sh
echo "===Finished test==="

echo "Please start server by running 'bash shell_scripts/start-server.sh'"
