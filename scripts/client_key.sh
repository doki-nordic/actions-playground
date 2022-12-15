#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

rm -f $2 > /dev/null 2> /dev/null
ssh-keygen -C ClientKey -N "" -t ed25519 -f $2
