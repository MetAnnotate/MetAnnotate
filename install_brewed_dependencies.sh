#!/usr/bin/env bash

# ======================================================================================================================
# Created by: Metannotate Team (2017)
#
# Description: A shell script for installing dependencies via Linux Brew.
#
# Requirements: - Linux Brew
# ======================================================================================================================

# Two brew updates to get around some bugs.
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
brew install pbzip2