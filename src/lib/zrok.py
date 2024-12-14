
import re
import time
import subprocess

import lib.conf as conf
from lib.proc import ProcessHandler, run_ret
from lib.utils import CallOnce, add_cleanup_command, download, untar
from lib.tunnel import ConnectionType, Tunnel

tar_file = conf.temp_dir / 'zrok.tar.gz'
exe_dir = conf.temp_dir / 'zrok'
exe_file = exe_dir / ('zrok.exe' if conf.is_windows else 'zrok')

global_prepare_once = CallOnce()

def global_prepare(_checked=False):
    if not _checked:
        return global_prepare_once.call(global_prepare, True)
    # Disable environment on cleanup
    add_cleanup_command(2, [exe_file, 'disable'])
    # Verify the token
    if conf.zrok_token is None:
        raise ValueError('Zrok token is not provided')
    # Download if does not exist
    if not exe_file.exists():
        download(conf.zrok_url, tar_file)
        untar(tar_file, exe_dir, 'gz')
        if not exe_file.exists():
            raise FileNotFoundError(f'Zrok executable not found at "{exe_file}"')
    # Check if enable is needed
    (status_stdout, status_stderr, _) = run_ret([exe_file, 'status'], check=True)
    # Enable if needed
    if (status_stdout + status_stderr).lower().find('use the zrok enable command') >= 0:
        subprocess.run([exe_file, 'enable', conf.zrok_token], check=True)
    # Show status
    subprocess.run([exe_file, 'status'], check=True)


class Zrok(Tunnel):

    _process: ProcessHandler

    def __init__(self):
        super().__init__()
        self._process = None
        self._buffer = b''
        self._info = {}
        self._name_reserved = False
        self._info_ready = False
        self.is_stopped = lambda: False

    def setup(self, name: str, type: ConnectionType, port: int, endpoint: str|None, client_port: int):
        super().setup(name, type, port, endpoint, client_port)
        global_prepare()
        if self.endpoint:
            p = re.sub(r'[^a-z0-9]', '', self.endpoint.lower())
            if p == '':
                self.endpoint = None
            elif len(p) < 4:
                self.endpoint = (p * 4)[:4]
            elif len(p) > 32:
                self.endpoint = p[:32]
            else:
                self.endpoint = p

    def start(self):
        self._buffer = b''
        if self.endpoint is not None:
            self._connect_with_prefix()
        else:
            self._connect_random()
        self._process.on_exit = self._process_on_exit
        self._process.on_stdout = self._process_on_stdout

    def stop(self):
        if self._process:
            self._process.terminate(10)

    def _connect_with_prefix(self):
        if not self._name_reserved:
            self._name_reserved = True
            add_cleanup_command(1, [exe_file, 'release', self.endpoint])
            ret: subprocess.Popen
            if self.type == ConnectionType.HTTP:
                ret = subprocess.run([exe_file, 'reserve', 'public', '-n', self.endpoint, str(self.port)], check=False)
            else:
                ret = subprocess.run([exe_file, 'reserve', 'private', '-b', 'tcpTunnel', '-n', self.endpoint, f'127.0.0.1:{self.port}'], check=False)
            if ret.returncode != 0:
                self.endpoint = None
                self._connect_random()
                return
        self._process = ProcessHandler([exe_file, 'share', 'reserved', '--headless', self.endpoint], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

    def _connect_random(self):
        if self.type == ConnectionType.HTTP:
            self._process = ProcessHandler([exe_file, 'share', 'public', '--headless', str(self.port)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
        else:
            self._process = ProcessHandler([exe_file, 'share', 'private', '-b', 'tcpTunnel', '--headless', f'127.0.0.1:{self.port}'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

    def _process_on_exit(self, process: subprocess.Popen, forced: bool):
        if forced:
            self.is_stopped = lambda: True
        else:
            print(f'Zrok exited unexpectedly with code {process.returncode}')
            time.sleep(1)
            self.start()

    def is_started(self):
        return self._info_ready

    def _process_on_stdout(self, data: bytes):
        if self._info_ready or (len(data) == 0):
            return
        self._buffer += data
        text = str(self._buffer, 'utf-8')
        url = None
        key = None
        for m in re.finditer(r'https?://[^\s"]*zrok[^\s"]*', text):
            url = m.group(0)
        for m in re.finditer(r'zrok access private[^"\r\n]*?[^a-z0-9_A-Z-]([a-z0-9]{4,32})[^a-z0-9_A-Z-]', text):
            key = m.group(1)
        if key is not None:
            self._info_ready = True
            self._info = {
                'info': f'\n```shell\nzrok access private -b 127.0.0.1:{self.client_port} {key}\n```\n',
                'host': '127.0.0.1',
                'port': str(self.client_port),
            }
        elif url is not None:
            self._info_ready = True
            self._info = {
                'info': f'[{url}]({url})'
            }
        else:
            self._info = { }

    def get_info(self) -> dict[str, str]:
        return self._info
