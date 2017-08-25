#!/bin/bash

echo -e "\nInstalling command-line version of metAnnotate...\n"

metAnnotateDir=`pwd`
software=`pwd`/software
PATH="${PATH}:${HOME}/.local/bin"

mkdir -p downloads
mkdir -p software
mkdir -p cache

echo -e "\nInstalling pip.\n"
if [ ! `which pip` ] ; then
  cd downloads
  wget "https://bootstrap.pypa.io/get-pip.py"
  # install pip locally
  python get-pip.py --user --ignore-installed
  cd ..
else
    echo "\nPip is already installed.\n"
fi

echo -e "\nInstalling python packages through pip.\n"
pip=`which pip`
if [ -e ~/.local/bin/pip ] ; then
  pip=~/.local/bin/pip
fi
$pip install --user -r requirements.txt --ignore-installed --quiet

echo -e "\nInstalling KronaTools.\n"
if [ ! `which ktImportText` ] ; then
  cd included_software/KronaTools-2.5/
  chmod a+x install.pl
  ./install.pl --prefix "${HOME}/.local/"
  chmod a+x scripts/*.pl
  cd $metAnnotateDir
else
  echo "\nKronaTools is already installed.\n"
fi

# Install linuxbrew and dependencies
./install_brewed_dependancies.sh

echo -e "\nInstalling USEARCH.\n"
if [ ! `which usearch` ] ; then
  echo "Changing execution permission on usearch"
  chmod a+x "${metAnnotateDir}/included_software/usearch"
  ln -s "${metAnnotateDir}/included_software/usearch" ~/.local/bin/usearch
else
  echo "\nUSEARCH already installed.\n"
fi

echo -e "\nInstalling pplacer and guppy.\n"
if [ ! `which guppy` ] ; then
  cd downloads
  wget "https://github.com/matsen/pplacer/releases/download/v1.1.alpha18/pplacer-linux-v1.1.alpha18-2-gcb55169.zip"
  echo "\nInstalling unzip.\n"
  if [ ! `which unzip` ]; then
    sudo apt-get -y install unzip
  else
    echo "\nUnzip already installed.\n"
  fi
  unzip pplacer*
  cd pplacer* && mv * ~/.local/bin/
  cd $metAnnotateDir
else
    echo "\nGuppy already installed.\n"
fi

echo -e "\nDownloading and indexing taxonomy info.\n"
if [ ! -e data/taxonomy.pickle ] ; then
  cd precompute
  wget "ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz"
  tar -zxf taxdump.tar.gz
  grep 'scientific name' names.dmp > trimmed.names.dmp
  python make_taxonomy_pickle.py
  cd $metAnnotateDir
else
    echo "\nRefseq taxonomy dump already cached.\n"
fi

echo -e "\nDownloading and indexing gi number to taxid mappings.\n"
if [ ! -e data/gi_taxid_prot.dmp ] ; then
  cd precompute
  wget "ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/gi_taxid_prot.dmp.gz"
  gunzip gi_taxid_prot.dmp.gz
  mv gi_taxid_prot.dmp ../data/
  cd $metAnnotateDir
else
  echo "\nTaxid mappings already cached.\n"
fi

echo -e "\nInstalling cronjob to clean cache. \n"
crontab -l > mycron # saving current cronjob
#echo new cron into cron file
# cleaning cache every monday at 5am
echo "# added by metannotate" >> mycron
echo "00 05 * * 1 cd ${metAnnotateDir} && bash shell_scripts/clean_cache.sh" >> mycron
#install new cron file
crontab mycron
rm mycron

rm -rf downloads
rm -f precompute/gc.prt
rm -f precompute/readme.txt
rm -f precompute/taxdump.tar.gz

echo "$HOME/.local/bin/" > path.txt

echo -e "Prerequisites have been installed and the command line version of metAnnotate has been set up."
echo -e "\nIMPORTANT: metAnnotate is still not fully ready to be run. You need to download the refseq database"
echo -e "and place it in the data directory (metannotate/data/) as \"Refseq.fa\". You also need to place the ssi"
echo -e "index of this file in the same directory, as \"Refseq.fa.ssi\". To build Refseq.fa, desired files can be"
echo -e "downloaded from \"ftp://ftp.ncbi.nlm.nih.gov/refseq/release/\" and concatenated. Alternatively, this fasta"
echo -e "file can be generated from local NCBI blastdb files. To create the ssi index, simply run \"esl-sfetch —index"
echo -e "Refseq.fa\ when in the data directory.\n"

echo -e "\nTo install the web UI version of metAnnotate, please run the full_installation.sh script with sudo permissions."
