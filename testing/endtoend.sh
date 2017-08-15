#!/usr/bin/env bash


sudo -S apt-mark hold sudo
sudo -S apt-mark hold procps
sudo -S apt-mark hold strace
echo "Running base install script"
cd ..
sudo -H bash base_installation.sh
sudo -H bash test_metannotate.sh