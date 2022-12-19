#!/bin/bash

# The script creates fifo at "/tmp/log" and redirects all
# incoming data to stdout.

mkfifo /tmp/log
while true; do cat < /tmp/log; done
