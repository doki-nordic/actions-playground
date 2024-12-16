
import re
import time
import subprocess

import lib.conf as conf
from lib.proc import ProcessHandler
from lib.utils import CallOnce, download, untar, unzip
from lib.tunnel import ConnectionType, Tunnel

arch_file = conf.temp_dir / ('bore.zip' if conf.is_windows else 'bore.tar.gz')
exe_file = conf.temp_dir / ('bore.exe' if conf.is_windows else 'bore')

global_prepare_once = CallOnce()

def global_prepare(_checked=False):
    if not _checked:
        return global_prepare_once.call(global_prepare, True)
    # Download if does not exist
    if not exe_file.exists():
        download(conf.bore_url, arch_file)
        if conf.is_windows:
            unzip(arch_file, exe_file.parent)
        else:
            untar(arch_file, exe_file.parent, 'gz')
        if not exe_file.exists():
            raise FileNotFoundError(f'Bore executable not found at "{exe_file}"')


class Bore(Tunnel):

    _process: ProcessHandler

    def __init__(self):
        super().__init__()
        self._process = None
        self._buffer = b''
        self._info = {}
        self._info_ready = False
        self._use_client_port = True
        self.is_stopped = lambda: False

    def setup(self, name: str, type: ConnectionType, port: int, endpoint: 'str|None', client_port: int):
        super().setup(name, type, port, endpoint, client_port)
        global_prepare()

    def start(self):
        self._buffer = b''
        self._connect()
        self._process.on_exit = self._process_on_exit
        self._process.on_stdout = self._process_on_stdout

    def stop(self):
        if self._process:
            self._process.terminate(10)

    def _connect(self):
        if self._use_client_port:
            self._process = ProcessHandler([exe_file, 'local', '-t', 'bore.pub', '-p', str(self.client_port), str(self.port)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
        else:
            self._process = ProcessHandler([exe_file, 'local', '-t', 'bore.pub', str(self.port)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

    def _process_on_exit(self, process: subprocess.Popen, forced: bool):
        if forced:
            self.is_stopped = lambda: True
        else:
            if self._use_client_port:
                print(f'Bore exited with code {process.returncode} - retrying with random port.')
                self._use_client_port = False
                self.start()
            else:
                print(f'Bore exited unexpectedly with code {process.returncode}')
                time.sleep(1)
                self.start()

    def is_started(self):
        return self._info_ready

    def _process_on_stdout(self, data: bytes):
        if self._info_ready or (len(data) == 0):
            return
        self._buffer += data
        text = str(self._buffer, 'utf-8')
        port = None
        for m in re.finditer(r'remote_port=([0-9]+)|bore\.pub:([0-9]+)', text):
            port = m.group(1) or m.group(2)
        if port is not None:
            self._info_ready = True
            self._info = {
                'host': 'bore.pub',
                'port': port,
            }
        else:
            self._info = { }

    def get_info(self) -> dict[str, str]:
        return self._info
