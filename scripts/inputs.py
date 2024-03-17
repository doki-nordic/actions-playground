

import json
from os import environ
from pathlib import Path
import platform
import re

scripts_dir = Path(__file__).parent
root_dir = scripts_dir.parent
data_dir = root_dir / 'data'
keys_dir = root_dir / 'keys'
if 'RUNNER_TEMP' in environ:
    temp_dir = Path(environ['RUNNER_TEMP'])
else:
    temp_dir = root_dir.parent

if platform.system() == 'Windows':
    bin_dir = Path(r'C:\Windows\System32')
else:
    bin_dir = Path(r'/usr/local/sbin')

wiki_dir = temp_dir / 'wiki'

contexts = json.loads((temp_dir / 'contexts.json').read_text())

shell: str = contexts['github']['event']['inputs']['shell']
os: str = contexts['github']['event']['inputs']['os']
windows: bool = os.startswith('windows')
ubuntu: bool = os.startswith('ubuntu')
macos: bool = os.startswith('macos')

def posix_path(input: 'str|Path') -> str:
    if windows:
        result = str(input).replace('\\', '/')
        if re.match(r'[A-Za-z]:', result):
            result = '/' + result[0].lower() + result[2:]
        return result
    else:
        return str(input)
