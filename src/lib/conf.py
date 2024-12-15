
import shutil
import platform
import configparser
from os import environ
from pathlib import Path
from types import SimpleNamespace

import lib.ctx as ctx

zrok_urls = {
    'windows': 'https://github.com/openziti/zrok/releases/download/v0.4.44/zrok_0.4.44_windows_amd64.tar.gz',
    'linux': 'https://github.com/openziti/zrok/releases/download/v0.4.44/zrok_0.4.44_linux_amd64.tar.gz',
    'darwin': 'https://github.com/openziti/zrok/releases/download/v0.4.44/zrok_0.4.44_darwin_amd64.tar.gz',
}

ttyd_urls = {
    'windows': 'https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.win32.exe',
    'linux': 'https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64',
    'darwin': None,
}

files_url = 'https://raw.githubusercontent.com/prasathmani/tinyfilemanager/refs/tags/2.6/tinyfilemanager.php'

#################################################################################

system = platform.system().lower()
is_windows = system == 'windows'
is_linux = system == 'linux'
is_macos = system == 'darwin'

if is_windows:
    user = 'runneradmin'
else:
    user = 'runner'

if not hasattr(ctx.secrets, 'PASSWORD'):
    raise ValueError('Missing PASSWORD in secrets')

scripts_dir = Path(__file__).parent.parent
root_dir = scripts_dir.parent
data_dir = root_dir / 'data'
keys_dir = root_dir / 'keys'
if 'RUNNER_TEMP' in environ:
    temp_dir = Path(environ['RUNNER_TEMP']).resolve()
else:
    temp_dir = root_dir.parent

zrok_url = zrok_urls[system]
ttyd_url = ttyd_urls[system]

if not is_windows and not is_linux and not is_macos:
    raise ValueError('Unsupported operating system')

def parse_settings_conf():
    result = {}
    if hasattr(ctx.vars, 'CONF'):
        config = configparser.ConfigParser()
        config.read_string('[conf]\n' + ctx.vars.CONF)
        for name, value in config['conf'].items():
            result[name.upper()] = str(value)
    for name, value in ctx.vars.__dict__.items():
        if name.upper() != 'CONF':
            result[name.upper()] = value
    return result

def get_value(name, default=None) -> 'str|None':
    name = name.upper()
    if name in settings_conf:
        return settings_conf[name]
    return default

settings_conf = parse_settings_conf()

ip_address = get_value('IP', None),

term = SimpleNamespace(
    endpoint=get_value('TERM_ENDPOINT', None),
    port=get_value('TERM_PORT', 80),
    client_port=get_value('TERM_CLIENT_PORT', 9980),
)

files = SimpleNamespace(
    endpoint=get_value('FILES_ENDPOINT', None),
    port=get_value('FILES_PORT', 81),
    client_port=get_value('FILES_CLIENT_PORT', 9981),
)

ssh = SimpleNamespace(
    endpoint=get_value('SSH_ENDPOINT', None),
    port=22,
    client_port=get_value('SSH_CLIENT_PORT', 9922),
)

rdp = SimpleNamespace(
    endpoint=get_value('RDP_ENDPOINT', None),
    port=3389,
    client_port=get_value('RDP_CLIENT_PORT', 9989),
)

try:
    sudo = shutil.which('sudo')
except:
    sudo = None
