#!/bin/bash

mkfifo /tmp/log
while true; do cat < /tmp/log; done &
