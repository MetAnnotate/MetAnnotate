#!/usr/bin/env bash

# The two possible paths to linuxbrew.
BREW_PATH_ONE=~/.linuxbrew
BREW_PATH_TWO=/home/linuxbrew/.linuxbrew

echo -e "\nInstalling Linuxbrew\n"
if [ ! -d "$BREW_PATH_ONE" ] && [ ! -d "$BREW_PATH_TWO" ] ; then
    yes | ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/linuxbrew/go/install)"
else
  echo "\nLinux brew is already installed.\n"
fi

echo -e "\nAttempting to add Brew to PATH\n"
if [ ! `which brew` ] ; then
    echo -e "\nAdding Brew to PATH\n"
    test -d ~/.linuxbrew && PATH="$HOME/.linuxbrew/bin:$PATH"
    test -d /home/linuxbrew/.linuxbrew && PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
    test -r ~/.bash_profile && echo 'export PATH="$(brew --prefix)/bin:$PATH"' >>~/.bash_profile
    echo 'export PATH="$(brew --prefix)/bin:$PATH"' >>~/.profile
else
  echo "\nLinux brew is already in the PATH.\n"
fi

brew update
brew update

brew tap homebrew/science
brew tap Metannotate/homebrew-metannotate
brew update

mkdir -p $HOME/.local/lib/python2.7/site-packages
echo "import site; site.addsitedir('$HOME/.linuxbrew/lib/python2.7/site-packages')" >> $HOME/.local/lib/python2.7/site-packages/homebrew.pth

brew install gcc
brew install emboss --without-x
brew install fasttree
brew install hmmer
brew install easel