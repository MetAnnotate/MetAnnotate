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
    echo -e "\nPip is already installed.\n"
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
  cd ${metAnnotateDir}
else
  echo -e "\nKronaTools is already installed.\n"
fi

echo -e "\nInstalling Brew and dependencies via ./install_brewed_dependencies.sh\n"
# Install linuxbrew and dependencies
./install_brewed_dependencies.sh

echo -e "\nInstalling USEARCH.\n"
if [ ! `which usearch` ] ; then
  echo "Changing execution permission on usearch"
  chmod a+x "${metAnnotateDir}/included_software/usearch"
  ln -s "${metAnnotateDir}/included_software/usearch" ~/.local/bin/usearch
else
  echo -e "\nUSEARCH already installed.\n"
fi

echo -e "\nInstalling pplacer and guppy.\n"
if [ ! `which guppy` ] ; then
  cd downloads
  wget "https://github.com/matsen/pplacer/releases/download/v1.1.alpha18/pplacer-linux-v1.1.alpha18-2-gcb55169.zip"
  echo -e "\nInstalling unzip.\n"
  if [ ! `which unzip` ]; then
    sudo apt-get -y install unzip
  else
    echo -e  "\nUnzip already installed.\n"
  fi
  unzip pplacer*
  cd pplacer* && mv * ~/.local/bin/
  cd ${metAnnotateDir}
else
    echo -e "\nGuppy already installed.\n"
fi

echo -e "\nInstalling cronjob to clean cache. \n"
if [ `crontab -l` ] ; then
    crontab -l > mycron # saving current cronjob
    #echo new cron into cron file
    # cleaning cache every monday at 5am
    echo "# added by metannotate" >> mycron
    echo "00 05 * * 1 cd ${metAnnotateDir} && bash shell_scripts/clean_cache.sh" >> mycron
    #install new cron file
    crontab mycron
    rm mycron
else
    echo -e "\nNo crontab found. Automated cache cleaning disabled. Please remember to clean your cache!\n"
fi

rm -rf downloads

echo "$HOME/.local/bin/" > path.txt

echo -e "The command line version of metAnnotate has been set up."
echo -e "\nIMPORTANT: Databases still need to be installed. Run refseq_installation.sh to do this."
echo -e "\nTo install the web UI version of metAnnotate, please run the web_UI_installation.sh script with sudo permissions."
