
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


def install_win_sshd():
    sshd_msi = conf.temp_dir / 'sshd.msi'
    if not sshd_msi.exists():
        download(conf.win_sshd_url, sshd_msi)
        subprocess.run(['msiexec', '/quiet', '/qn', '/i', str(sshd_msi)], check=True, shell=True)


def get_ssh_keys():
    keys_raw = [
        *conf.get_multi_value("SSH_KEYS"),
        *conf.get_multi_value("SSH_KEY"),
        *conf.get_multi_value("CLIENT_KEYS"),
        *conf.get_multi_value("CLIENT_KEY")
        ]
    keys_joined = '\n'.join(keys_raw).encode() + b'\n'
    keys_joined += (conf.keys_dir / 'client_key.pub').read_bytes()
    keys_text = keys_joined.replace(b';', b'\n').replace(b'\r', b'\n')
    keys_arr = keys_text.split(b'\n')
    keys_clean = [key.strip() for key in keys_arr if len(key.strip()) > 0]
    keys_unique = set(keys_clean)
    return b'\n'.join(keys_unique) + b'\n'


class ServiceSSH(Service):

    def setup(self, tunnel: Tunnel):
        super().setup(tunnel)
        tunnel.setup('ssh', ConnectionType.SSH, conf.ssh.port, conf.ssh.endpoint, conf.ssh.client_port)
        if conf.is_windows:
            install_win_sshd()
            subprocess.run(['net', 'stop', 'sshd'], check=False)
            self.ssh_keys_dir = Path('C:\\ProgramData\\ssh')
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
        client_pub = get_ssh_keys()
        if not authorized_keys_file.exists():
            authorized_keys_file.parent.mkdir(parents=True, exist_ok=True)
            authorized_keys_file.write_bytes(client_pub)
            authorized_keys_file.chmod(0o644)
        else:
            separator = b'' if authorized_keys_file.read_bytes().endswith(b'\n') else b'\n'
            with open(authorized_keys_file, 'ab') as dst:
                dst.write(separator + client_pub + b'\n')
        if conf.is_windows:
            admin_keys = self.ssh_keys_dir / 'administrators_authorized_keys'
            if not admin_keys.exists():
                admin_keys.write_bytes(client_pub)
                subprocess.run([
                    shutil.which('icacls'), admin_keys,
                    '/inheritance:r',
                    '/grant', 'Administrators:F',
                    '/grant', 'SYSTEM:F'], check=True)
            else:
                separator = b'' if admin_keys.read_bytes().endswith(b'\n') else b'\n'
                with open(admin_keys, 'ab') as dst:
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
