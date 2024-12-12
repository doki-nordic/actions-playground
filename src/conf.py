
import platform
from os import environ
from pathlib import Path
from types import SimpleNamespace

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

#################################################################################

system = platform.system().lower()
is_windows = system == 'windows'
is_linux = system == 'linux'
is_macos = system == 'darwin'

scripts_dir = Path(__file__).parent
root_dir = scripts_dir.parent
data_dir = root_dir / 'data'
keys_dir = root_dir / 'keys'
if 'RUNNER_TEMP' in environ:
    temp_dir = Path(environ['RUNNER_TEMP']).resolve()
else:
    temp_dir = root_dir.parent

zrok_url = zrok_urls[system]
zrok_token = environ['ZROK_TOKEN'] if 'ZROK_TOKEN' in environ else None

ttyd_url = ttyd_urls[system]

if not is_windows and not is_linux and not is_macos:
    raise ValueError('Unsupported operating system')

def _get_service_config(prefix: str):
    return SimpleNamespace(
        endpoint=environ.get(f'{prefix}_ENDPOINT', None),
        port=int(environ.get(f'{prefix}_PORT', 80)),
        client_port=int(environ.get(f'{prefix}_CLIENT_PORT', 9980)),
    )

term = _get_service_config('TERM')
