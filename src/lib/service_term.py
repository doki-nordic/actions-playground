
import time
import shutil
import subprocess
from pathlib import Path

import lib.conf as conf
import lib.ctx as ctx
from lib.service import Service
from lib.proc import ProcessHandler
from lib.utils import download, firewall_open, get_environment
from lib.tunnel import ConnectionType, Tunnel


class ServiceTerm(Service):

    def setup(self, tunnel: Tunnel):
        super().setup(tunnel)
        tunnel.setup('term', ConnectionType.HTTP, conf.term.port, conf.term.endpoint, conf.term.client_port)
        if conf.is_linux:
            self.exe_file = conf.temp_dir / 'ttyd'
            if not self.exe_file.exists():
                download(conf.ttyd_url, self.exe_file)
                self.exe_file.chmod(0o755)
        elif conf.is_windows:
            self.exe_file = conf.temp_dir / 'ttyd.exe'
            if not self.exe_file.exists():
                download(conf.ttyd_url, self.exe_file)
        elif conf.is_macos:
            try:
                self.exe_file = Path(shutil.which('ttyd'))
            except:
                subprocess.run(['brew', 'install', 'ttyd'], check=True, shell=True)
                self.exe_file = Path(shutil.which('ttyd'))
        firewall_open(conf.term.port, self.exe_file)

    def start(self):
        self._start_process()
        self.tunnel.start()

    def _start_process(self):
        self._process = ProcessHandler([
                self.exe_file,
                '--writable',
                '--debug', '0',
                '--port', str(conf.term.port),
                '--cwd', ctx.github.workspace,
                '--credential', f'{conf.user}:{ctx.secrets.PASSWORD}',
                shutil.which(ctx.inputs.shell),
            ],
            env=get_environment(ctx.github.workspace),
            cwd=ctx.github.workspace)
        self._process.on_exit = self._process_on_exit

    def _process_on_exit(self, process: subprocess.Popen, forced: bool):
        if not forced:
            time.sleep(1)
            self._start_process()

    def is_started(self):
        return self.tunnel.is_started()

    def stop(self):
        self.tunnel.stop()
        self._process.terminate(10)

    def is_stopped(self):
        return self.tunnel.is_stopped() and self._process.is_terminated()
