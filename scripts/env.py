# The script create a shell script file that reproduces specific
# environment variables.

import os
import re
from pathlib import Path
from argparse import ArgumentParser
from utils import bash_escape, cmd_escape

parser = ArgumentParser()
parser.add_argument('--bat', help='output file as Windows batch file')
parser.add_argument('--bash', help='output file as Bash script')
parser.add_argument('--env-out', help='output environment in format the same as "env -0"')
parser.add_argument('--ctx', help='additional file with context')
parser.add_argument('--env-filter', help='input environment from current environment with regex as a filter')
parser.add_argument('--env-file', help='input environment from file, the format is the same as an output of "env -0"')
parser.add_argument('--skip', nargs='*', default=[], help='skip specific variables names, each argument is a name')
parser.add_argument('--cd', help='change current directory at the end of the script')
args = parser.parse_args()

if (args.bat is None) and (args.bash is None):
    parser.print_help()
    exit(1)

def get_env():
    if args.env_filter is None:
        return []
    result = []
    for key, value in os.environ.items():
        if re.fullmatch(args.env_filter, key):
            result.append((key, value))
    return result

def get_env_file():
    if args.env_file is None:
        return []
    text = Path(args.env_file).read_text(errors='replace')
    result = []
    for item in text.split('\0'):
        item = item.split('=', 1)
        if len(item) < 2:
            continue
        key, value = item
        result.append((key, value))
    return result

def get_ctx():
    if args.ctx is None:
        return []
    text = Path(args.ctx).read_text(errors='replace')
    result = []
    for part in text.split('aSsIgNCtXVaR:'):
        part = part.lstrip()
        while (len(part) > 0) and (ord(part[-1:]) <= 32) and (part[-1:] != '\n'):
            part = part[0:-1]
        if (len(part) > 0) and (part[-1] == '\n'):
            part = part[0:-1]
            if (len(part) > 0) and (part[-1] == '\r'):
                part = part[0:-1]
        pos = part.find('=')
        if pos < 0:
            continue
        key = part[0:pos]
        value = part[pos+1:]
        result.append((key, value))
    return result

def add_var(key, value):
    global output_bash, output_cmd
    if key in args.skip:
        return
    output_cmd += f'set {key}={cmd_escape(value)}\r\n'
    if re.fullmatch(r'[A-Z_a-z][0-9A-Z_a-z]*', key):
        output_bash += f'export {key}=$\'{bash_escape(value)}\'\n'

output_bash = '#!/bin/bash\n'
output_cmd = '@echo off\r\n'

for key, value in get_env_file():
    add_var(key, value)

for key, value in get_env():
    add_var(key, value)

for key, value in get_ctx():
    add_var(key, value)

if args.cd is not None:
    output_bash += f'cd $\'{bash_escape(args.cd)}\'\n'
    output_cmd += f'cd /d {cmd_escape(args.cd)}\r\n'

if args.bat is not None:
    Path(args.bat).write_text(output_cmd)

if args.bash is not None:
    p = Path(args.bash)
    p.write_text(output_bash)
    p.chmod(0o755)
