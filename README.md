Table of Contents
=========================

**[Support and Requirements](#markdown-header-support-and-requirements)**  
**[metAnnotate Modes](#markdown-header-modes)**  
**[Installing Base/Command Line Version](#markdown-header-base-installation)**  
**[Concurrency](#markdown-header-concurrency)**  
**[Built-in Webserver](#markdown-header-built-in-webserver)**  
**[Configure With Apache and Celeryd](#markdown-header-configure-with-apache-and-celeryd)**  

Installation Instructions
=========================

Support and Requirements
------------------------
Debian/Ubuntu, with at least 6GB of space + the space required to store the Refseq database.

The following packages should already be installed on your system (if not they can be installed with 'sudo apt-get install'):

 * python-dev
 * build-essential
 * default-jre
 * git

Modes
-----

metAnnotate can be run in different ways. The simplest way to run metAnnotate is
via command line, which produces a number or output tables and html krona
charts. However, metAnnotate can be run as a webserver to provide a rich UI that
can be used to analyze all results. Currently, users must have sudo permissions
to install the additional requirements necessary to run the server. We hope to
remove this requirement in the future. The web server can be run as a standalone
web server, or can be integrated with apache so that it runs on startup all the
time. See the installation instructions for all three modes below.

Base Installation
-----------------
To install:

    git clone https://bitbucket.org/doxeylab/metannotate.git
    cd metannotate
    bash base_installation.sh

Note that you will also need to setup the Refseq.fa and Refseq.fa.ssi file in
the metannotate/data/ directory. To build Refseq.fa, desired files can be
downloaded from <ftp://ftp.ncbi.nlm.nih.gov/refseq/release/> and concatenated like this:

    cd data/
    #This might take a few hours
    wget ftp://ftp.ncbi.nlm.nih.gov/refseq/release/complete/complete.nonredundant_protein*.protein.faa.gz
    zcat *.faa.gz >Refseq.fa
    
To create the ssi index, simply run:

    ~/.local/bin/esl-sfetch --index Refseq.fa

Or, if you already had esl-sfetch available on your system:

    esl-sfetch --index Refseq.fa

Alternatively, you can download a 2014 refseq file and index like this (very slow):

    wget http://scopepc.uwaterloo.ca/Refseq.fa # 9.1 GB
    wget http://scopepc.uwaterloo.ca/Refseq.fa.ssi # 1.3 GB

Sample run:

    python run_metannotate.py --orf_files=data/MetagenomeTest.fa --hmm_files=data/hmms/RPOB.HMM --reference_database=data/ReferenceTest.fa --output_dir=test_output --tmp_dir=test_tmp --run_mode=both

Or simply:

    bash test_metannotate.sh

Note that in the example above, a [tiny] test reference database was specified. If not specified, the default data/Refseq.fa database is used. More options:

    python run_metannotate.py --help

Concurrency
-----------
You can speed up metannotate by specifying a greater concurrency in metannotate/concurrency.txt. This will have the effect of increasing concurrency for HMMER, FastTree, and pplacer commands.

Built-in Webserver
------------------
To install, first follow the base installation instructions above, and then run
the following script in the metannotate directory:

    sudo bash full_installation.sh

To finish the installation, you will still need to configure the metagenome
directory files. You need to create 2 files:

 * metagenome\_directories\_root.txt
 * metagenome\_directories.txt
 
See metagenome\_directories\_sample.txt and
metagenome\_directories\_root\_sample.txt for reference. These files need to be
placed in the main metannotate direcoty (current directory).
metagenome\_directories\_root.txt contains the root path for all metagenome
directories that will be read by the program. metagenome\_directories.txt lists
all the directories in that root directory that should be read as metagenome
directories (in the case that you have other directories in the root directory
that shouldn't be interpreted as metagenome directories).

To run:

    python app.wsgi local >out.txt 2>&1 &  

The output will contain both web server and celery output.

Configure with Apache and Celeryd
---------------------------------

Configuring the app to run with an Apache server and an existing celery daemon
process is safer and ensures that the tool runs on startup. 

### Create a Celery Daemon Process

 * sudo adduser celery
 * sudo passwd celery \# Create a password. Remember it for the next step.
 * vim celery.pw \# Add celery password to file.
 * sudo adduser celery www-data
 * Install https://raw.githubusercontent.com/celery/celery/3.1/extra/generic-init.d/celeryd into /etc/init.d/celeryd
 * sudo chmod a+x /etc/init.d/celeryd
 * sudo vim /etc/default/celeryd

```
# Names of nodes to start
#   most will only start one node:
CELERYD_NODES="worker1"

#CELERY_RESULT_BACKEND='amqp://'
CELERY_TASK_RESULT_EXPIRES=172800

# Absolute or relative path to the 'celery' command:
CELERY_BIN="/usr/local/bin/celery"

# App instance to use
CELERY_APP="tasks"

# Where to chdir at start.
CELERYD_CHDIR=""  # Change as needed to directory containing tasks.py.

# Extra command-line arguments to the worker
CELERYD_OPTS="--concurrency=1"

# %N will be replaced with the first part of the nodename.
CELERYD_LOG_FILE="/var/log/celery/%N.log"
CELERYD_PID_FILE="/var/run/celery/%N.pid"

# Workers should run as an unprivileged user.
#   You need to create this user manually (or you can choose
#   a user/group combination that already exists, e.g. nobody).
CELERYD_USER="celery"
CELERYD_GROUP="celery"

# If enabled pid and log directories will be created if missing,
# and owned by the userid/group configured.
CELERY_CREATE_DIRS=1
```

 * sudo update-rc.d celeryd defaults
 * sudo /etc/init.d/celeryd restart

### Integrating with Apache.
 * sudo apt-get install libapache2-mod-wsgi
 * sudo vim /etc/apache2/sites-available/000-default.conf

```
<VirtualHost *:80>
  #ServerName www.example.com

  ServerAdmin webmaster@localhost
  DocumentRoot /var/www/html

  WSGIDaemonProcess metannotate
  WSGIProcessGroup metannotate
  WSGIScriptAlias / /path/to/app.wsgi # Change as needed.

  <Directory /path/to/dir/containing/app.wsgi> # change as needed.
    Options All
    AllowOverride All
    Require all granted
  </Directory>

  ErrorLog ${APACHE_LOG_DIR}/error.log
  CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```

### Change Permissions of IO Directories.
 * sudo chgrp www-data realinput/
 * sudo chown www-data realinput/
 * sudo chmod g+w realinput/
 * sudo chgrp www-data input/
 * sudo chown www-data input/
 * sudo chmod g+w input/
 * sudo chgrp www-data output/
 * sudo chown www-data output/
 * sudo chmod g+w output/
 * sudo chgrp www-data databases/
 * sudo chown www-data databases/
 * sudo chmod g+w databases/
 * sudo chgrp www-data tmp/
 * sudo chown www-data tmp/
 * sudo chmod g+w tmp/
 * sudo chgrp www-data session/
 * sudo chown www-data session/
 * sudo chmod g+w session/

### Restarting
Upon a restart of the system, all components will be restarted as well. If
necessary, the components can be restarted manually using the following
commands:

 * sudo /etc/init.d/rabbitmq-server restart
 * sudo /etc/init.d/celeryd restart
 * sudo /etc/init.d/apache2 reload
