Table of Contents
=========================

**[Support and Requirements](#markdown-header-support-and-requirements)**  
**[Installing Base/Command Line Version](#markdown-header-base-installation)** 
**[Concurrency](#markdown-header-concurrency)**  
**[Built-in Webserver](#markdown-header-built-in-webserver)**  
**[A Note on Cache](#markdown-header-a-note-on-cache)**  
**[Known Issues](#markdown-header-known-issues)**  
**[Configure With Apache and Celeryd](#markdown-header-configure-with-apache-and-celeryd)**  

Installation Instructions
=========================

Packaged Installation (Simpler)
---
This is a simpler to install with [Docker](https://www.docker.com/) packaging (similar to running in virtual box). However, you won't be able to (or it is inconvenient to) use the command line version of MetAnntoate. 

It works on a Mac and on Linux, however, be sure that your laptop meets required RAM and space requirement. 

*Follow instructions here* https://bitbucket.org/doxeylab/metannotateinstaller

The rest of the README is for Ubuntu 14.04+ users with fair technical knowledge. It is _required_ if you want to use the command line version of MetAnnotate. 



Support and Requirements
------------------------
Debian/Ubuntu, with at least 6GB of space + the space required to store the Refseq database.

The following packages are required. Note that in [One Command Install](#markdown-header-one-command-install), the dependencies are _automatically_installed

 * python-dev (version 2.7)
 * build-essential
 * default-jre
 * git
 * wget
 * python-mysqldb 
 * rabbitmq-server 
 * libssl-dev 
 * libffi-dev 
 * sqlite3



One Command Install (install all dependencies, command-line and webserver)
----

For Ubuntu:14.04: 

*NOTE* machine root password is required and will be asked for

Step 1: 
```bash
sudo apt-get update
if [ ! `which git` ]; then
  sudo apt-get install -y git
fi
git clone --depth=1 https://bitbucket.org/doxeylab/metannotate.git
cd metannotate
bash one_command_install.sh
# enter password as required
```


Sample run:
---

    python run_metannotate.py --orf_files=data/MetagenomeTest.fa --hmm_files=data/hmms/RPOB.HMM --reference_database=data/ReferenceTest.fa --output_dir=test_output --tmp_dir=test_tmp --run_mode=both

Note that in the example above, a [tiny] test reference database was specified to make process faster. If not specified, the default data/Refseq.fa database is used. You should now see run outputs in `test_output` directory. 


For more options:

    python run_metannotate.py --help

Concurrency
-----------
You can speed up metannotate by specifying a greater concurrency in metannotate/concurrency.txt. This will have the effect of increasing concurrency for HMMER, FastTree, and pplacer commands.

Built-in Webserver
------------------
The web server is installed as part of *One Command Install*

There are two files that provide additional configuration:

 * metagenome\_directories\_root.txt
 * metagenome\_directories.txt
 
These files are already placed in the main metannotate directory.

metagenome\_directories\_root.txt contains the root path for all metagenome
directories that will be read by the program. metagenome\_directories.txt lists
all the directories in that root directory that should be read as metagenome
directories (in the case that you have other directories in the root directory
that shouldn't be interpreted as metagenome directories).

To start server:

    bash start-server.sh 
    # enter password as prompted

To stop server: 

    bash stop.sh
    # enter password as prompted


Output of server is at `out.txt` for debugging purposes.

Occasionally (when no job is running), you can run `rm tmp/*` to free up disk space. 



A Note on Cache
----

MetAnnotate has a cache layer that is cleaned every week. You can modify your Cronjob by typing `crontab -e` to edit the clean up interval. 

Repeating the same HMM files is much faster with cache (95% speed up). 

Known Issues
----

If an ORF file has no HMM hit, the script will terminate and job will error out.



Configure with Apache and Celeryd (More technical)
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
