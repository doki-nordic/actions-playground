
import sys
from utils import cmd2bash

sys.stdout.write(cmd2bash(sys.argv[1]))
