
import time
import shutil
import subprocess

import lib.conf as conf
import lib.ctx as ctx
from lib.service import Service
from lib.proc import ProcessHandler
from lib.utils import download, firewall_open
from lib.tunnel import ConnectionType, Tunnel


class ServiceFiles(Service):

    def setup(self, tunnel: Tunnel):
        super().setup(tunnel)
        tunnel.setup('files', ConnectionType.HTTP, conf.files.port, conf.files.endpoint, conf.files.client_port)
        self.app_dir = conf.temp_dir / 'tinyfilemanager'
        self.app_dir.mkdir(parents=True, exist_ok=True)
        download(conf.files_url, self.app_dir / 'index.php')
        config_file = self.app_dir / 'config.php'
        pwd = ctx.secrets.PASSWORD.replace('\\', '\\\\').replace('\'', '\\\'').strip()
        config_file.write_text(f'''<?php
            $auth_users=array(
                'runner' => password_hash('{pwd}', PASSWORD_DEFAULT),
                'runneradmin'=> password_hash('{pwd}', PASSWORD_DEFAULT)
            );
            $root_path="/./";
            $CONFIG = '{"{"}"lang":"en","error_reporting":false,"show_hidden":true,"hide_Cols":false,"theme":"dark"{"}"}';
            $readonly_users = array();
            '''.strip())
        firewall_open(conf.files.port, shutil.which('php'))
        #   TODO: Windows
        #   mkdir D:\DiskC
        #   echo select volume C: > conf.txt
        #   echo assign mount=D:\DiskC >> conf.txt
        #   diskpart < conf.txt

    def start(self):
        self._start_process()
        self.tunnel.start()

    def _start_process(self):
        args = [
            shutil.which('php'),
            '-S', f'127.0.0.1:{conf.files.port}',
            '-t', self.app_dir
        ]
        if not conf.is_windows:
            args.insert(0, conf.sudo)
        self._process = ProcessHandler(args)
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
