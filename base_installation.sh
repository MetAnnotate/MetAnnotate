#!/bin/bash

echo "Installing command-line version of metAnnotate...\n"

mkdir downloads
mkdir software
software=`pwd`/software

echo "Installing pip.\n"
cd downloads
cd python-pip-*
python setup.py install --user
PATH="${PATH}:${HOME}/.local/bin"
cd ..
cd ..

echo "Installing EMBOSS transeq.\n"
cd downloads
wget ftp://emboss.open-bio.org/pub/EMBOSS/emboss-latest.tar.gz
tar -xzf emboss-latest.tar.gz
cd EMBOSS*
./configure --without-x
make
cp -R emboss/ "$software"/
ln -s "$software"/emboss/transeq ~/.local/bin/transeq
cd ..
cd ..

echo "Installing python packages through pip.\n"
pip install --user celery
pip install --user taxtastic
pip install —-user lxml

echo "Installing KronaTools.\n"
./included_software/KronaTools-2.5/install.pl —prefix="${HOME}/.local/"

echo "Installing HMMER & Easel mini-applications.\n"
cd downloads
wget "ftp://selab.janelia.org/pub/software/hmmer3/3.1b1/hmmer-3.1b1-linux-intel-x86_64.tar.gz"
tar -xzf hmmer-3.1b1-linux-intel-x86_64.tar.gz
cd hmmer*
./configure
make
cp -R . "$software"/hmmer/
ln -s "$software"/hmmer/binaries/hmmstat ~/.local/bin/hmmstat
ln -s "$software"/hmmer/binaries/hmmsearch ~/.local/bin/hmmsearch
ln -s "$software"/hmmer/binaries/hmmalign ~/.local/bin/hmmalign
ln -s "$software"/hmmer/binaries/esl-reformat ~/.local/bin/esl-reformat
ln -s "$software"/hmmer/binaries/esl-sfetch ~/.local/bin/esl-sfetch
cd ..
cd ..

echo "Installing USEARCH.\n"
ln -s `pwd`"/included_software/usearch" ~/.local/bin/usearch

echo "Installing USEARCH.\n"
cd downloads
wget "http://www.microbesonline.org/fasttree/FastTreeMP"
mv FastTreeMP ~/.local/bin/
chmod a+x ~/.local/bin/FastTreeMP
cd ..

echo "Installing pplacer and guppy.\n"
cd downloads
wget "http://matsen.fhcrc.org/pplacer/builds/pplacer-v1.1-Linux.tar.gz"
tar -xzf pplacer-v1.1-Linux.tar.gz 
cd pplacer*
mv pplacer ~/.local/bin/
mv guppy ~/.local/bin/
cd ..
cd ..

echo "Downloading and indexing taxonomy info.\n"
cd precompute
wget "ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz"
tar -zxf taxdump.tar.gz
grep 'scientific name' names.dmp > trimmed.names.dmp
python make_taxonomy_pickle.py
cd ..

echo "Downloading and indexing gi number to taxid mappings.\n"
cd precompute
wget "ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/gi_taxid_prot.dmp.gz"
gunzip gi_taxid_prot.dmp.gz
mv gi_taxid_prot.dmp ../data/
cd ..

rm -rf downloads
rm -f precompute/gc.prt
rm -f precompute/readme.txt
rm -f precompute/taxdump.tar.gz

echo "$HOME/.local/bin/" > path.txt

echo -e "Prerequisites have been installed and the command line version of metAnnotate has been set up.\n\nIMPORTANT: metAnnotate is still not fully ready to be run. You need to download the refseq database and place it in the data directory (metannotate/data/) as \"Refseq.fa\". You also need to place the ssi index of this file in the same directory, as \"Refseq.fa.ssi\". To build Refseq.fa, desired files can be downloaded from \"ftp://ftp.ncbi.nlm.nih.gov/refseq/release/\" and concatenated. Alternatively, this fasta file can be generated from local NCBI blastdb files. To create the ssi index, simply run \"esl-sfetch —index Refseq.fa\" when in the data directory.\n\nTo install the web UI version of metAnnotate, please run the full_installation.sh script with sudo permissions."
