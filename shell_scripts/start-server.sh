#!/bin/bash

if [ ! `which rabbitmq-server` ];then
    if [[ ! -x "/usr/sbin/rabbitmq-server" ]]; then 
        >&2 echo "rabbitmq-server must be installed by sudo apt-get install rabbitmq-server"
        exit 1
    fi
    # add directory to PATH
    export PATH=/usr/sbin:$PATH
    echo 'export PATH=/usr/sbin:$PATH #added by metannotate' >> $HOME/.bashrc
fi

echo "Checking rabbitmq-server status"
sudo rabbitmqctl status &> /dev/null #don't want to confuse user with error message
rabbitStatus=$?

if [ $rabbitStatus -ne 0 ]; then
    echo "starting server"
    sudo rabbitmq-server -detached
fi

echo "rabbitmq-server started"

if [ `whoami` == "root" ];then 
    export C_FORCE_ROOT="true"
fi

echo "starting server, killing previous one"
if [ -r "server.pid" -a -s "server.pid" ];then 
    kill `cat server.pid` # kill previous server
fi
nohup python app.wsgi local >out.txt 2>&1 &
# saving app pid 
echo `ps -ef | grep "python app.wsgi local" | head -1 | awk '{print $2}'` > server.pid
echo "server started at `cat server.pid`"



