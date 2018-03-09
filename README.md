[![Gitter chat](https://badges.gitter.im/Metannotate.png)](https://gitter.im/Metannotate)


Installing MetAnnotate
=========================

MetAnnotate can be used either as a command line tool or as a web UI (hosted by your server).

Requirements
------------------------
**Operating system**: Debian/Ubuntu

**Disk space**: >= 6 GiB of disk space + space to store the Refseq database (~20 GiB as of Jan. 2018).

**Dependencies**:
* [linuxbrew](http://linuxbrew.sh) -- see install instructions at the link provided
* python-dev (2.7.x) -- e.g., `sudo apt-get install -y python-dev`
* OR [docker-ce](https://docs.docker.com/install/linux/docker-ce/ubuntu/) if using the Docker container (above dependencies not needed in this case)
 
 Other dependencies are added **automatically** during installation:
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

Recommended: Docker installation for command line and (soon) web GUI
---
**NOTE**: Web GUI is not yet supported for Docker in this fork. Please be patient.

This install relies on [Docker](https://www.docker.com/) to avoid common installation errors. Installing via Docker allows you to run MetAnnotate in a virtual machine-like environment on your server.

The Docker installation should work on any operating system supporting Docker (e.g., Mac OSX, Linux, or Windows, provided that you have sufficient disk space and RAM as stated in the Requirements), although only Linux has been tested. 

Get started with:
```
docker run -it jmtsuji/metannotate:latest /bin/bash
```

To use the command line effectively, you'll need to mount system file directories into the Docker container. This is handled by the friendly wrapper included in this repo, `enter-metannotate`. This will enter the Docker container for you. Simply add the script to your ordinary system PATH (as shown below) and run the entry command:

```
git clone -b linuxbrew https://github.com/Metannotate/Metannotate.git
cd Metannotate
chmod 755 enter-metannotate
sudo cp enter-metannotate /usr/local/bin # or add to your path a different way, or use locally only.
rm -r Metannotate # if only using Docker, the rest of the git repo is not needed. Might need sudo to delete the git repo.

enter-metannotate # to see informative help file that goes into more detail than presented here
enter-metannotate [path_to_RefSeq_directory] [path_to_ORF_directory] [path_to_HMM_directory] [path_to_output_directory]
```

Example command line usage:
```
# Download RefSeq database (only needed on first use):
enter-metannotate [path_to_RefSeq_directory] [path_to_ORF_directory] [path_to_HMM_directory] [path_to_output_directory]
refseq_installation.sh /home/linuxbrew/databases
exit

# Start MetAnnotate run via the simple command line wrapper (run metannotate-wrapper-docker for more detailed help):
enter-metannotate [path_to_RefSeq_directory] [path_to_ORF_directory] [path_to_HMM_directory] [path_to_output_directory]
metannotate-wrapper-docker [run_type] [path_to_orf_files] [path_to_hmm_files] 2>&1 | tee metannotate_wrapper_docker.log
exit
```

Complete (non-Docker) installation (command line and web UI)
------------------------

```bash
#cd to home directory
sudo apt-get update
if [ ! `which git` ]; then
  sudo apt-get install -y git
fi
git clone -b linuxbrew https://github.com/Metannotate/Metannotate.git
cd Metannotate
bash one_command_install.sh
# enter password as required
```
**Note**: This is still untested in this fork of MetAnnotate (undergoing code base improvements)

Command line (non-Docker) installation
------------------------

If you wish to install only the command line version of MetAnnotate, please run the following code:

```bash
#cd to home directory
sudo apt-get update
if [ ! `which git` ]; then
  sudo apt-get install -y git
fi
git clone -b linuxbrew https://github.com/Metannotate/Metannotate.git
cd Metannotate
bash base_installation.sh
bash refseq_installation.sh # to install databases
# enter password as required
```

You can then run `run_metannotate.py` from within the install folder (does not work if run outside the install folder). Try `run_metannotate.py -h` for options.


Running MetAnnotate
=========================

Command line example -- advanced usage
---
```
# cd [metannotate_repo_directory]
run_metannotate.py --orf_files=data/MetagenomeTest.fa --hmm_files=data/hmms/RPOB.HMM --reference_database=data/ReferenceTest.fa --output_dir=test_output --tmp_dir=test_tmp --run_mode=both
```
Note that in the example above, a (tiny) test reference database was specified to make process faster. If not specified, the default data/Refseq.fa database is used. You should now see run outputs in `test_output` directory. 

For more options:
```
python run_metannotate.py --help
```

Command line example -- simplified
---
You lose access to more advanced settings like e-value cutoffs using the provided wrappers, but you gain much in simplicity:

```
# Standard wrapper
metannotate-wrapper [metannotate_dir] [RefSeq_dir] [run_type] [path_to_orf_files] [path_to_hmm_files] [output_dir] 2>&1 | tee metannotate_wrapper.log

# Even simpler wrapper that works with enter-metannotate (see above)
metannotate-wrapper-docker [run_type] [path_to_orf_files] [path_to_hmm_files] 2>&1 | tee metannotate_wrapper_docker.log
```

Threads (concurrency)
-----------
You can speed up metannotate by specifying a greater concurrency (number of threads) in Metannotate/concurrency.txt. This will have the effect of increasing concurrency for HMMER, FastTree, and pplacer commands.

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
