#!/usr/bin/env bash


sudo -S apt-mark hold sudo
sudo -S apt-mark hold procps
sudo -S apt-mark hold strace

echo "\n============================="
echo "Running base install script"
echo "=============================\n"
cd ..

# if statement for avoiding the miserable gid_taxid_prot.dmp download
if [ ! -f /data/gi_taxid_prot.dmp ];
then
    echo "========================================================="
    echo "No data cache detected, running full base_installation.sh"
    echo "========================================================="
    sudo -H bash base_installation.sh

else
    echo "============================================================="
    echo "Data cache detected, running abbreviated base_installation.sh"
    echo "============================================================="
    cd testing
    sudo -H bash base_installation_for_test.sh
    cd ..
fi

sudo -H bash test_metannotate.sh