#!/usr/bin/env bash
set -euxo pipefail

# ======================================================================================================================
# Created by: Metannotate Team (2017)
#
# Description: A shell script for installing dependencies via Linuxbrew.
#
# Requirements: - Linux Brew
# ======================================================================================================================

# Brew update twice to get around some bugs that occur with fresh brew installs.
brew update
brew update

brew tap brewsci/science # TODO: confirm whether this can be removed.
brew tap brewsci/bio
brew tap Metannotate/homebrew-metannotate
brew update

mkdir -p $HOME/.local/lib/python2.7/site-packages
echo "import site; site.addsitedir('$HOME/.linuxbrew/lib/python2.7/site-packages')" >> $HOME/.local/lib/python2.7/site-packages/homebrew.pth

brew install --force-bottle gcc
brew install linuxbrew/xorg/xorg
brew install emboss --without-x
brew install fasttree
brew install hmmer
brew install metannotate/metannotate/easel
brew install pbzip2
