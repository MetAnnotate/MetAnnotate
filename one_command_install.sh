#!/bin/bash

echo "Installing commandline and web version of metAnnotate, along with database"
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

echo "===Testing newly installed metannotate==="
bash test_metannotate.sh
# should expect 2 annotation files in test_output
count=0
for file in rpoB_0_MetagenomeTest_0_annotations_*.tsv; do count=$((count+1)); done
if [ $count -ne 1 ]; then
    >&2 echo "Testing failed, please check the output for error. Did you have the right permission to files? "
    exit 1
fi

echo "=======Test passed====="

echo "Please start server by running 'bash shell_scripts/start-server.sh'"
