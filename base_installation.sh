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
fi

# The two possible paths to linuxbrew.
BREW_PATH_ONE=~/.linuxbrew
BREW_PATH_TWO=/home/linuxbrew/.linuxbrew

echo -e "\nInstalling Linuxbrew\n"
if [ ! -d "$BREW_PATH_ONE" ] && [ ! -d "$BREW_PATH_TWO" ] ; then
    yes | ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/linuxbrew/go/install)"
fi

echo -e "\nAttempting to add Brew to PATH\n"
if [ ! `which brew` ] ; then
    echo -e "\nAdding Brew to PATH\n"
    test -d ~/.linuxbrew && PATH="$HOME/.linuxbrew/bin:$PATH"
    test -d /home/linuxbrew/.linuxbrew && PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
    test -r ~/.bash_profile && echo 'export PATH="$(brew --prefix)/bin:$PATH"' >>~/.bash_profile
    echo 'export PATH="$(brew --prefix)/bin:$PATH"' >>~/.profile
fi

brew tap homebrew/science
brew install emboss --without-x

echo -e "\nInstalling HMMER & Easel mini-applications.\n"
if [ ! `which hmmsearch` ] | [ ! `which esl-sfetch` ] ; then
  cd downloads
  wget "http://eddylab.org/software/hmmer3/3.1b2/hmmer-3.1b2-linux-intel-x86_64.tar.gz" #updated address here
  tar --no-same-owner -xzf hmmer-3.1b2-linux-intel-x86_64.tar.gz
  cd hmmer*
  ./configure
  make
  cp -R . "$software"/hmmer/
  ln -s "$software"/hmmer/binaries/hmmstat ~/.local/bin/hmmstat
  ln -s "$software"/hmmer/binaries/hmmsearch ~/.local/bin/hmmsearch
  ln -s "$software"/hmmer/binaries/hmmalign ~/.local/bin/hmmalign
  ln -s "$software"/hmmer/binaries/esl-reformat ~/.local/bin/esl-reformat
  ln -s "$software"/hmmer/binaries/esl-sfetch ~/.local/bin/esl-sfetch
  cd $metAnnotateDir
fi

echo -e "\nInstalling USEARCH.\n"
if [ ! `which usearch` ] ; then
  echo "Changing execution permission on usearch"
  chmod a+x "${metAnnotateDir}/included_software/usearch"
  ln -s "${metAnnotateDir}/included_software/usearch" ~/.local/bin/usearch
fi

echo -e "\nInstalling FastTreeMP.\n"
if [ ! `which FastTreeMP` ] ; then
  cd downloads
  wget "http://www.microbesonline.org/fasttree/FastTreeMP"
  mv FastTreeMP ~/.local/bin/
  chmod a+x ~/.local/bin/FastTreeMP
  cd $metAnnotateDir
fi

echo -e "\nInstalling pplacer and guppy.\n"
if [ ! `which guppy` ] ; then
  cd downloads
  wget "https://github.com/matsen/pplacer/releases/download/v1.1.alpha18/pplacer-linux-v1.1.alpha18-2-gcb55169.zip"
  if [ ! `which unzip` ]; then
    sudo apt-get -y install unzip
  fi
  unzip pplacer*
  cd pplacer* && mv * ~/.local/bin/
  cd $metAnnotateDir
fi

echo -e "\nDownloading and indexing taxonomy info.\n"
if [ ! -e data/taxonomy.pickle ] ; then
  cd precompute
  wget "ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz"
  tar -zxf taxdump.tar.gz
  grep 'scientific name' names.dmp > trimmed.names.dmp
  python make_taxonomy_pickle.py
  cd $metAnnotateDir
fi

echo -e "\nDownloading and indexing gi number to taxid mappings.\n"
if [ ! -e data/gi_taxid_prot.dmp ] ; then
  cd precompute
  wget "ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/gi_taxid_prot.dmp.gz"
  gunzip gi_taxid_prot.dmp.gz
  mv gi_taxid_prot.dmp ../data/
  cd $metAnnotateDir
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
