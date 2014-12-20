Table of Contents
=========================

**[Support](#support)**  
**[Prerequisites](#prerequisites)**  
**[Installing](#installing)**  
**[Built-in Webserver](#built-in-webserver)**  
**[Configure With Apache and Celeryd](#configure-with-apache-and-celeryd)**  

Installation Instructions
=========================

Support
-------
Debian/Ubuntu.


Prerequisites
-------------
These are programs that need to exist already on your linux machine before
trying to install/run metAnnotate.

### Apt-get and pip installations.

 * sudo apt-get install python-pip python-dev build-essential
 * sudo apt-get install python-mysqldb
 * sudo apt-get install rabbitmq-server
 * sudo apt-get install sqlite3
 * sudo apt-get install default-jre
 * sudo apt-get install emboss  
 * sudo pip install celery
 * sudo pip install bottle
 * sudo pip install beaker
 * sudo pip install ete2
 * sudo pip install paramiko
 * sudo pip install biopython
 * sudo pip install taxtastic  
 * sudo pip install lxml

### Install Krona Tools
This is used to visualize the distribution of organisms found.

 * Download from http://sourceforge.net/projects/krona/files/KronaTools%20%28Mac%2C%20Linux%29/
 * tar -xvf KronaTools.tar
 * sudo mv KronaTools-2.4 /usr/lib/
 * cd /usr/lib/KronaTools-2.4
 * sudo ./install.pl

### Install HMMER and easel mini-applications
HMMER contains the main HMM searching tools used, and also contains other tools
to convert between file formats.

 * wget ftp://selab.janelia.org/pub/software/hmmer3/3.1b1/hmmer-3.1b1-linux-intel-x86_64.tar.gz  
 * tar -xzvf hmmer-3.1b1-linux-intel-x86_64.tar.gz  
 * cd hmmer-3.1b1-linux-intel-x86_64  
 * ./configure  
 * make  
 * sudo make install  
 * cd easel  
 * sudo make install  
  
### Install usearch  
USEARCH provides a fast BLAST-like search approach.

 * Request a copy here: http://www.drive5.com/usearch/download.html  
 * sudo mv usearch7.0.1090_i86linux32 /usr/bin/usearch  
 * sudo chmod a+x /usr/bin/usearch  
  
### Install FastTreeMP  
This is used when building trees from HMM alignments.

 * wget http://www.microbesonline.org/fasttree/FastTreeMP  
 * sudo mv FastTreeMP /usr/bin/FastTreeMP  
 * sudo chmod a+x /usr/bin/FastTreeMP  
  
### Install pplacer
Used to place new sequences onto an existing tree topology.

 * wget http://matsen.fhcrc.org/pplacer/builds/pplacer-v1.1-Linux.tar.gz  
 * tar -xzvf pplacer-v1.1-Linux.tar.gz  
 * cd pplacer-v1.1.alpha16-1-gf748c91-Linux-3.2.0/  
 * sudo mv guppy /usr/bin/  
 * sudo mv pplacer /usr/bin/  

Installing
----------

git clone <repository path>

### Link Reference Fasta File
 * add or link Refseq.fa to data/
 * esl-sfetch —index Refseq.fa, or link Refseq.fa.ssi

### Download and Index HMMs
 * cd precompute/
 * wget ftp://ftp.jcvi.org/pub/data/TIGRFAMs/GEN_PROP/PROP_DEF_WITHOUT_DESCRIPTION_FIELD.TABLE
 * wget ftp://ftp.jcvi.org/pub/data/TIGRFAMs/GEN_PROP/PROP_GO_LINK.TABLE
 * wget ftp://ftp.jcvi.org/pub/data/TIGRFAMs/GEN_PROP/PROP_STEP.TABLE
 * wget ftp://ftp.jcvi.org/pub/data/TIGRFAMs/GEN_PROP/STEP_EV_LINK.TABLE
 * wget ftp://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/Pfam-A.hmm.gz
 * gunzip Pfam-A.hmm.gz
 * python pfam_splitter.py
 * wget ftp://ftp.jcvi.org/pub/data/TIGRFAMs/TIGRFAMs_15.0_HMM.tar.gz
 * tar -xzvf TIGRFAMs_15.0_HMM.tar.gz -C ../data/hmms/
 * python make_hmms_json.py

### Download and Index Taxonomy Info
 * wget ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz
 * tar -zxvf taxdump.tar.gz
 * grep 'scientific name' names.dmp > trimmed.names.dmp
 * python make_taxonomy_pickle.py

### Download GI to Taxid Mapping
 * wget ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/gi_taxid_prot.dmp.gz
 * gunzip gi_taxid_prot.dmp.gz
 * mv gi_taxid_prot ../data/

### Set Metagenome Directories
 * cd ..
 * cp metagenome_directories_root_sample.txt metagenome_directories_root.txt
 * vim metagenome_directories_root.txt
 * cp metagenome_directories_sample.txt metagenome_directories.txt
 * vim metagenome_directories.txt

Running
=======

Built-in Webserver
------------------
You can run the app using a simple built in webserver provided by bottle. This
will start a celery process that will queue and run all the tasks that you
create.  

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
 * sudo chgrp www-data input/
 * sudo chown www-data input/
 * sudo chgrp www-data output/
 * sudo chown www-data output/
 * sudo chgrp www-data databases/
 * sudo chown www-data databases/
 * sudo chgrp www-data tmp/
 * sudo chown www-data tmp/
 * sudo chgrp www-data session/
 * sudo chown www-data session/

### Restarting
Upon a restart of the system, all components will be restarted as well. If
necessary, the components can be restarted manually using the following
commands:

 * sudo /etc/init.d/rabbitmq-server restart
 * sudo /etc/init.d/celeryd restart
 * sudo /etc/init.d/apache2 reload
