[![Gitter chat](https://badges.gitter.im/Metannotate.png)](https://gitter.im/Metannotate)

Table of Contents
=========================

**[Installing MetAnnotate](#Installing-MetAnnotate)**  
**[Running MetAnnotate](#Running-MetAnnotate)** 
**[Additional usage notes](#Additional-usage-notes)**  
**[Advanced: alternative web server configurations](#Advanced:-alternative-web-server-configurations)**  

Installing MetAnnotate
=========================

MetAnnotate can be used either as a command line tool or as a web UI (hosted by your server).

Requirements
------------------------
**Operating system**: Debian/Ubuntu

**Disk space**: >= 6 GiB of disk space + space to store the Refseq database (~20 GiB as of Jan. 2018).

**Dependencies**: [linuxbrew](http://linuxbrew.sh) must be installed prior to using MetAnnotate.
 
 Other dependencies are added **automatically** during installation:
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
 * ...and so on.

Complete installation (command line and web UI)
------------------------

```bash
#cd to home directory
sudo apt-get update
if [ ! `which git` ]; then
  sudo apt-get install -y git
fi
git clone --depth=1 https://bitbucket.org/doxeylab/metannotate.git
cd metannotate
bash one_command_install.sh
# enter password as required
```

Command line installation
------------------------

If you wish to install only the command line version of MetAnnotate, please run the following code:

```bash
#cd to home directory
sudo apt-get update
if [ ! `which git` ]; then
  sudo apt-get install -y git
fi
git clone --depth=1 https://bitbucket.org/doxeylab/metannotate.git
cd metannotate
bash base_installation.sh
bash refseq_installation.sh # to install databases
# enter password as required
```

You can then run `metannotate.py` from within the install folder.


Docker installation (simpler, for web UI only)
---
**Recommended for users with less coding experience who only need the web UI version of MetAnnotate**

This install relies on [Docker](https://www.docker.com/)to avoid common installation errors and allows you to access the web UI version of MetAnnotate. Installing via Docker allows you to run MetAnnotate in a virtual machine-like environment on your server.

(It is still possible but is inconvenient to use the command line version of MetAnnotate when installing in this way.) 

The Docker installation works on both Mac (OSX) and on Linux (provided that you have sufficient disk space and RAM -- see Requirements above). 

*Follow instructions here* https://bitbucket.org/doxeylab/metannotateinstaller


Running MetAnnotate
=========================

Command line example
---

    python run_metannotate.py --orf_files=data/MetagenomeTest.fa --hmm_files=data/hmms/RPOB.HMM --reference_database=data/ReferenceTest.fa --output_dir=test_output --tmp_dir=test_tmp --run_mode=both

Note that in the example above, a (tiny) test reference database was specified to make process faster. If not specified, the default data/Refseq.fa database is used. You should now see run outputs in `test_output` directory. 


For more options:

    python run_metannotate.py --help

Concurrency
-----------
You can speed up metannotate by specifying a greater concurrency (number of threads) in metannotate/concurrency.txt. This will have the effect of increasing concurrency for HMMER, FastTree, and pplacer commands.

Web UI (web server)
------------------
After installing MetAnnotate via `one_command_install.sh` (see above), you'll need to configure and start the web server before it is usable.

**Configuration**: you need to specify the locations on the server where metagenomes will be stored using the following files: 

 * metagenome\_directories\_root.txt
 * metagenome\_directories.txt
 
These files are already placed in the main MetAnnotate directory.

`metagenome_directories_root.txt` contains the root path for all metagenome
directories that will be read by the program. `metagenome_directories.txt` lists
all the directories in that root directory that should be read as metagenome
directories (in the case that you have other directories in the root directory
that shouldn't be interpreted as metagenome directories).

**Starting and stopping the server**:

To start the server:

    bash start-server.sh 
    # enter password as prompted

To stop the server: 

    bash stop.sh
    # enter password as prompted


Output of server is at `out.txt` for debugging purposes.

Occasionally (when no job is running), you can run `rm tmp/*` to free up disk space. 


Additional usage notes
=========================

A Note on Cache
----

MetAnnotate has a cache layer that is cleaned every week. You can modify your Cronjob by typing `crontab -e` to edit the clean up interval. 

Repeating the same HMM files is much faster with cache (95% speed up). 


Known Issues
----

If an ORF file has no HMM hit, the script will terminate and job will error out.


Advanced: alternative web server configurations
=========================

Configuring the web UI with Apache and Celeryd (more technical)
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
