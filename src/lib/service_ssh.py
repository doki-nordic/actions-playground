
import time
import shutil
import subprocess
from pathlib import Path

import lib.conf as conf
import lib.ctx as ctx
from lib.service import Service
from lib.proc import ProcessHandler
from lib.utils import as_root, download, firewall_open, unpack_keys
from lib.tunnel import ConnectionType, Tunnel


def replace_host_keys(ssh_keys_dir: Path):
    for dst_pub_file in ssh_keys_dir.glob('ssh_host_*_key.pub'):
        dst_prv_file = dst_pub_file.with_suffix('')
        src_pub_file = conf.keys_dir / dst_pub_file.name
        src_prv_file = conf.keys_dir / dst_prv_file.name
        if (not dst_prv_file.exists()) or (not src_pub_file.exists()) or (not src_prv_file.exists()):
            continue
        with open(dst_prv_file, 'rb+') as dst:
            dst.truncate(0)
            dst.write(src_prv_file.read_bytes())
        with open(dst_pub_file, 'rb+') as dst:
            dst.truncate(0)
            dst.write(src_pub_file.read_bytes())


class ServiceSSH(Service):

    def setup(self, tunnel: Tunnel):
        super().setup(tunnel)
        tunnel.setup('ssh', ConnectionType.SSH, conf.ssh.port, conf.ssh.endpoint, conf.ssh.client_port)
        if conf.is_windows:
            subprocess.run(['net', 'stop', 'sshd'], check=True)
            self.ssh_keys_dir = Path('.') # TODO: keys path in windows
        elif conf.is_linux:
            subprocess.run([conf.sudo, 'systemctl', 'disable', '--now', 'ssh.socket'])
            subprocess.run([conf.sudo, 'systemctl', 'stop', 'ssh'], check=True)
            self.ssh_keys_dir = Path('/etc/ssh')
        elif conf.is_macos:
            pass # TODO: stop service in macOS
            self.ssh_keys_dir = Path('.') # TODO: keys path in macOS
        unpack_keys()
        as_root(replace_host_keys, self.ssh_keys_dir)
        authorized_keys_file = Path.home() / '.ssh/authorized_keys'
        client_pub = (conf.keys_dir / 'client_key.pub').read_bytes()
        if not authorized_keys_file.exists():
            authorized_keys_file.parent.mkdir(parents=True, exist_ok=True)
            authorized_keys_file.write_bytes(client_pub)
            authorized_keys_file.chmod(0o644)
        else:
            separator = b'' if authorized_keys_file.read_bytes().endswith(b'\n') else b'\n'
            with open(authorized_keys_file, 'ab') as dst:
                dst.write(separator + client_pub + b'\n')

    def start(self):
        self.tunnel.start()
        if conf.is_windows:
            subprocess.run(['net', 'start', 'sshd'], check=True)
        elif conf.is_linux:
            subprocess.run([conf.sudo, 'systemctl', 'enable', '--now', 'ssh.socket'])
            subprocess.run([conf.sudo, 'systemctl', 'start', 'ssh'], check=True)
        elif conf.is_macos:
            pass # TODO: start service in macOS

    def is_started(self):
        return self.tunnel.is_started()

    def stop(self):
        self.tunnel.stop()

    def is_stopped(self):
        return self.tunnel.is_stopped()
