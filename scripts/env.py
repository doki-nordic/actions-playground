
import os
import sys
import re
import utils
from os.path import dirname

#
# The script reads environment variables from current environment
# and ctx_vars.txt file. Next, it outputs shell scripts that reproduce
# the the environment variables.
#

skip_vars = ('_', 'PWD')
parent_dir = dirname(__file__) + '/..'
bash_file = f'{parent_dir}/job_vars'
bat_file = f'{parent_dir}/job_vars.bat'
ctx_file = f'{parent_dir}/ctx_vars.txt'


def cmd_escape(text):
    return (text
        .replace('%', '%%')
        .replace('^', '^^')
        .replace('&', '^&')
        .replace('<', '^<')
        .replace('>', '^>')
        .replace('|', '^|')
        .replace('\'', '^\'')
        .replace('`', '^`')
        .replace(',', '^,')
        .replace(';', '^;')
        .replace('=', '^=')
        .replace('(', '^(')
        .replace(')', '^)')
        .replace('"', '^"')
        .replace('\r\n', '\n')
        .replace('\n', '^\r\n\r\n')
        )

def add_var(key, value):
    global output_bash, output_cmd
    if key in skip_vars:
        return
    output_cmd += f'set {key}={cmd_escape(value)}\r\n'
    if re.fullmatch(r'[0-9A-Z_a-z]*', key):
        if re.fullmatch(r'[\+,\-\.\/0-9:=A-Z_a-z]*', value):
            output_bash += f'export {key}={value}\n'
        else:
            output_bash += f"read -r -d '' {key} <<'EnDOfThIssTrIng'\n{value}\nEnDOfThIssTrIng\n"
            output_bash += f"export {key}\n"

def process_ctx_file(text: str):
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
        add_var(key, value)

output_bash = '#!/bin/bash\n'
output_cmd = '@echo off\r\n'

for key, value in os.environ.items():
    add_var(key, value)

with open(ctx_file, 'r') as fd:
    process_ctx_file(fd.read())

dest = sys.argv[1]

output_bash += f'cd "{utils.cmd2bash(dest)}"\n'
output_cmd += f'cd /d "{dest}"\r\n'

with open(bash_file, 'w') as fd:
    fd.write(output_bash)
os.chmod(bash_file, 0o755)

with open(bat_file, 'w') as fd:
    fd.write(output_cmd)
