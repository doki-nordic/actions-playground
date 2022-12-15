#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

rm -f $SCRIPT_DIR/../host_key > /dev/null 2> /dev/null
ssh-keygen -C HostKey -N "" -t ed25519 -f $SCRIPT_DIR/../host_key
zerotier-idtool generate $SCRIPT_DIR/../identity.secret
$SCRIPT_DIR/client_key.sh $SCRIPT_DIR/../client_key

if [ "$1" == "host_key" ]; then


elif [ "$1" == "client_key" ]; then

	rm -f $2 > /dev/null 2> /dev/null
	ssh-keygen -C ClientKey -N "" -t ed25519 -f $2

elif [ "$1" == "identity" ]; then


elif [ "$1" == "conf" ]; then

	awk '{sub("---DIR---","'"$SCRIPT_DIR"'")}1' $SCRIPT_DIR/sshd.template.conf > $SCRIPT_DIR/sshd.conf
	awk '{sub("---USER---","'`whoami`'")}1' $SCRIPT_DIR/exit_job.template > $SCRIPT_DIR/exit_job
	chmod 755 $SCRIPT_DIR/exit_job
	python3 $SCRIPT_DIR/copy_env.py $SCRIPT_DIR/job_vars

elif [ "$1" == "all" ]; then

	$SCRIPT_DIR/manage.sh host_key
	$SCRIPT_DIR/manage.sh client_key $SCRIPT_DIR/client_key
	$SCRIPT_DIR/manage.sh identity

else

	echo "Usage:"
	echo "$0 host_key         Create new host key"
	echo "$0 client_key file  Create new client key"
	echo "$0 conf             Create configuration file with paths set to this directory"
	echo "$0 all              Create both keys at once"

fi
