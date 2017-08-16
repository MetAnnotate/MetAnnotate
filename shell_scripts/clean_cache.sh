#!/bin/bash

for file in cache/* ; do
    # if no process is using it, remove it
    if [[ ! `lsof ${file} 2>/dev/null` ]]; then 
        rm $file
    fi
done


