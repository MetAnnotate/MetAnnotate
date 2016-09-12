#!/bin/bash

echo "Installing commandline and web version of metAnnotate, along with database"
echo "This is going to need root access and will take a while."
metAnnotateDir="`pwd`"

if [ ! `which wget` ]; then
    sudo apt-get -y install wget
fi

sudo apt-get install -y python-dev build-essential default-jre

bash ./base_installation.sh
bash ./full_installation.sh

cd ${metAnnotateDir}/data
echo "Checking Refseq database being downloaded"
#This might take a few hours
if [ ! -e "Refseq.fa" ] || [ ! -e "Refseq.fa.ssi" ]; then
    echo "downloading refseq db, will take a few hours"
    wget ftp://ftp.ncbi.nlm.nih.gov/refseq/release/complete/complete.nonredundant_protein*.protein.faa.gz
    zcat *.faa.gz >Refseq.fa
    ~/.local/bin/esl-sfetch --index Refseq.fa
fi

cd ${metAnnotateDir}
mkdir -p "${HOME}/metagenome_files/sample"
echo "${HOME}/metagenome_files" > metagenome_directories_root.txt
echo "${HOME}/metagenome_files/sample" > metagenome_directories.txt

echo "===Testing newly installed metannotate==="
bash test_metannotate.sh
# should expect 2 annotation files in test_output
count=0
for file in rpoB_0_MetagenomeTest_0_annotations_*.tsv; do count=$((count+1)); done
if [ $count -ne 2 ]; then
    >&2 echo "Testing failed, please check the output for error. Did you have the right permission to files? "
    exit 1
fi

echo "=======Test passed====="

rabbitmq-server -detached
nohup python app.wsgi local >out.txt 2>&1 &
# saving app pid 
echo `ps -ef | grep "python app.wsgi local" | head -1 | awk '{print $2}'` > server.pid


