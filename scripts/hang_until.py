# This script waits until something is created at location specified by the first argument.

import sys
from pathlib import Path
from time import sleep

on_file = Path(sys.argv[1])

while not on_file.exists():
    sleep(5)
