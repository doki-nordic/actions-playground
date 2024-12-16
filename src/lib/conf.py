
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

bore_urls = {
    'windows': 'https://github.com/ekzhang/bore/releases/download/v0.5.2/bore-v0.5.2-x86_64-pc-windows-msvc.zip',
    'linux': 'https://github.com/ekzhang/bore/releases/download/v0.5.2/bore-v0.5.2-x86_64-unknown-linux-musl.tar.gz',
    'darwin': 'https://github.com/ekzhang/bore/releases/download/v0.5.2/bore-v0.5.2-x86_64-apple-darwin.tar.gz',
}

ttyd_urls = {
    'windows': 'https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.win32.exe',
    'linux': 'https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64',
    'darwin': None,
}

files_url = 'https://raw.githubusercontent.com/prasathmani/tinyfilemanager/refs/tags/2.6/tinyfilemanager.php'

win_sshd_url = 'https://github.com/PowerShell/Win32-OpenSSH/releases/download/v9.8.1.0p1-Preview/OpenSSH-Win64-v9.8.1.0.msi'

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
bore_url = bore_urls[system]
ttyd_url = ttyd_urls[system]

if not is_windows and not is_linux and not is_macos:
    raise ValueError('Unsupported operating system')


settings_conf = {}
settings_vars = {}
settings_secrets = {}

def parse_settings_conf():
    global settings_conf, settings_vars, settings_secrets
    if hasattr(ctx.vars, 'CONF'):
        config = configparser.ConfigParser()
        config.read_string('[conf]\n' + ctx.vars.CONF)
        for name, value in config['conf'].items():
            settings_conf[name.upper()] = str(value)
    for name, value in ctx.vars.__dict__.items():
        if name.upper() != 'CONF':
            settings_vars[name.upper()] = value
    for name, value in ctx.secrets.__dict__.items():
        settings_secrets[name.upper()] = value

parse_settings_conf()

def get_value(name, default=None) -> 'str|None':
    name = name.upper()
    if name in settings_vars:
        return settings_vars[name]
    if name in settings_secrets:
        return settings_secrets[name]
    if name in settings_conf:
        return settings_conf[name]
    return default

def get_multi_value(name) -> 'list[str]|None':
    name = name.upper()
    res = []
    if name in settings_vars:
        res.append(settings_vars[name])
    if name in settings_secrets:
        res.append(settings_secrets[name])
    if name in settings_conf:
        res.append(settings_conf[name])
    return res

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
