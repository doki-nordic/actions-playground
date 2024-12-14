
import sys
import subprocess

import lib.conf as conf

file_list = []

for file in conf.temp_dir.glob('*.cleanup'):
    parts = file.name.split('.')
    order = int(parts[-2])
    file_list.append((order, file))

file_list.sort(key=lambda x: x[0])

for _, file in file_list:
    try:
        subprocess.run([sys.executable, conf.scripts_dir / 'do_remote_call.py', file])
    finally:
        file.unlink()
