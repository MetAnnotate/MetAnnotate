Table of Contents
=========================

**[Support and Requirements](#markdown-header-support-and-requirements)**  
**[metAnnotate Modes](#markdown-header-modes)**  
**[Installing Base/Command Line Version](#markdown-header-base-installation)**  
**[Built-in Webserver](#markdown-header-built-in-webserver)**  
**[Configure With Apache and Celeryd](#markdown-header-configure-with-apache-and-celeryd)**  

Installation Instructions
=========================

Support and Requirements
------------------------
Debian/Ubuntu.

The following packages should already be installed on your system:

 * python-dev
 * build-essential
 * default-jre
 * git

Modes
-----

Base Installation
-----------------
To install:

    git clone https://bitbucket.org/doxeylab/metannotate.git
    cd metannotate
    bash base_installation.sh

Note that you will also need to setup the Refseq.fa and Refseq.fa.ssi file in
the metannotate/data/ directory. To build Refseq.fa, desired files can be
downloaded from ftp://ftp.ncbi.nlm.nih.gov/refseq/release/ and comcatenated.
Alternatively, this fasta file can be generated from local NCBI blastdb files.
To create the ssi index, simply run:

    esl-sfetch —index Refseq.fa

Sample run:

    python run_metannotate.py --orf_files=../sample_metagenomes/4478943.3.transeq.fa --hmm_files=data/hmms/TIGR00665.HMM --output_dir=my_output --tmp_dir=my_tmp

More options:

    python run_metannotate.py --help

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
that shouldn't be interpreted as metagenome directories)."

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
