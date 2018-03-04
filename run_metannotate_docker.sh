#!/bin/bash
# Description: Wrapper to run metannotate command line through a Docker container

# Basic script stuff (Buffalo, 2017):
set -e
set -u
set -o pipefail

script_version=1.0.0
date_code=$(date '+%y%m%d')

# If input field is empty, print help and end script
if [ $# == 0 ]; then
    printf "$(basename $0): wrapper to run metannotate command line from inside a docker container.\n"
    printf "Wrapper version: ${script_version}\n"
    printf "Contact Jackson Tsuji (jackson.tsuji@uwaterloo.ca; Neufeld research group) for error reports or feature requests.\n\n"
    printf "Usage: $(basename $0) < install | download | run >\n\n"
    printf "Install: Installs the command line version of MetAnnotate in a docker container named metannotate/metannotate\n"
    printf "Download: Downloads the RefSeq database (needed before first use of MetAnnotate). This will also install MetAnnotate via docker if not already installed.\n"
    printf "Run: After this, input the settings you would add for using run_metannotate.py. Your run will then be executed from within the docker container.\n\n"
    exit 1
fi

#################################################################
##### Global variables: #########################################
RUN_MODE=$1
CONTAINER_NAME="metannotate/metannotate:dev1"
#################################################################

### NOT YET FINISHED ###



##echo "Running $(basename $0) version $script_version on ${date_code} (yymmdd). Will use ${threads} threads (hard-coded into script for now)."
##echo ""
#
## Test that /path/to/metagenome/directory exists, and exit if it does not
#if [ ! -d ${fastq_dir} ]; then
## From http://stackoverflow.com/a/4906665, accessed Feb. 4, 2017
#    print "Did not find /path/to/metagenome/directory exists ${fastq_dir}. Job terminating."
#    exit 1
#fi
#
## Test that /path/to/output/directory exists, and exit if it does not
#if [ ! -d ${output_dir} ]; then
## From http://stackoverflow.com/a/4906665, accessed Feb. 4, 2017
#    print "Did not find /path/to/output/directory ${output_dir}. Job terminating."
#    exit 1
#fi
#
## Test that /path/to/output/directory/tmp exists, and exit if it does not
#if [ ! -d ${output_dir}/tmp ]; then
## From http://stackoverflow.com/a/4906665, accessed Feb. 4, 2017
#    print "Did not find /path/to/output/directory/tmp ${output_dir}/tmp. Please make this folder before starting. Job terminating."
#    exit 1
#fi
#
#start_time=$(date)
#
## Start the container (will this work??? Not yet tested - 171218)
#docker run -v ${database_dir}:/home/atlas/databases \
#-v ${fastq_dir}:/home/atlas/data \
#-v ${output_dir}:/home/atlas/output \
#-it jmtsuji/atlas:version1
#
#end_time=$(date)
#
#echo ""
#echo ""
#echo "Done."
#echo ""
#
#echo "$(basename $0): finished."
#echo "Started at ${start_time} and finished at ${end_time}."
#echo ""
