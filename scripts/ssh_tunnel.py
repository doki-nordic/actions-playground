
import re
import os
import subprocess
import shutil
import time

from enum import Enum
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future

class Service(Enum):
    PINGGY_HTTP = 0
    PINGGY_TCP = 1
    LOCALHOST_RUN_HTTP = 2


class SshTunnelAddresses:
    http_url: 'str | None' = None
    https_url: 'str | None' = None
    tcp_address: 'str | None' = None
    tcp_port: 'int | None' = None


def read_pipe(file):
    return file.read1()


class SshTunnelBase:

    proc: 'subprocess.Popen | None'
    buffer: bytearray
    poll_result: 'SshTunnelAddresses | None' = None
    executor: 'ThreadPoolExecutor | None' = None
    future: 'Future | None' = None

    def __init__(self, port: int=80, ssh_path: str='ssh'):
        self.port = port
        self.ssh_path = shutil.which(ssh_path)
        self.proc = None
        self.reconnect_time = time.monotonic()
        self.buffer = bytearray()
        if not hasattr(os, 'set_blocking'):
            self.executor = ThreadPoolExecutor(1)

    def get_args(self):
        pass

    def process_output(self):
        pass

    def start(self):
        args = self.get_args()
        print('TUNNEL: Starting SSH:', args[0:-1])
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
        if hasattr(os, 'set_blocking'):
            os.set_blocking(self.proc.stdout.fileno(), False)

    def poll(self) -> 'SshTunnelAddresses | None':
        self.poll_result = None
        if (self.proc is None) and (self.reconnect_time <= time.monotonic()):
            self.start()
        if self.proc is not None:
            while True:
                if self.executor:
                    if not self.future:
                        self.future = self.executor.submit(read_pipe, self.proc.stdout)
                    if self.future.done():
                        output = self.future.result()
                        self.future = self.executor.submit(read_pipe, self.proc.stdout)
                        if (output is not None) and (len(output) > 0):
                            self.buffer += output
                            self.process_output()
                    else:
                        break
                else:
                    if (self.proc.poll() is None) and self.proc.stdout.readable():
                        output = self.proc.stdout.read()
                        if (output is None) or (len(output) == 0):
                            break
                        else:
                            self.buffer += output
                            self.process_output()
                    else:
                        break
            ret = self.proc.poll()
            if ret is not None:
                print('TUNNEL: SSH unexpectedly exited with code.', ret)
                self.reconnect_time = time.monotonic() + 1
                self.proc = None
        if self.poll_result:
            print('TUNNEL: New addresses:')
            if self.poll_result.http_url:
                print(f'    HTTP:  {self.poll_result.http_url}')
            if self.poll_result.https_url:
                print(f'    HTTPS: {self.poll_result.https_url}')
            if self.poll_result.tcp_address:
                print(f'    TCP:   {self.poll_result.tcp_address}:{self.poll_result.tcp_port}')
        return self.poll_result

    def exit(self):
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
        if self.proc is not None:
            try:
                try:
                    self.proc.stdin.close()
                except:
                    pass
                try:
                    self.proc.stdout.close()
                except:
                    pass
                print('TUNNEL: Terminating SSH.')
                self.proc.terminate()
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                try:
                    print('TUNNEL: Killing SSH.')
                    self.proc.kill()
                    self.proc.wait(5)
                except subprocess.TimeoutExpired:
                    pass
            finally:
                self.proc = None


class Pinggy(SshTunnelBase):

    def __init__(self, port: int=80, http: bool=True, token: 'str | None'=None, ssh_path: str='ssh'):
        super().__init__(port, ssh_path)
        self.http = http
        self.token = token

    def get_args(self):
        if self.http:
            if self.token and len(self.token):
                user = f'{self.token}@'
            else:
                user = f''
        else:
            if self.token and len(self.token):
                user = f'{self.token}+tcp@'
            else:
                user = 'tcp@'
        args = [
            self.ssh_path,
            '-p', '443',
            f'-R0:localhost:{self.port}',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ServerAliveInterval=30',
            '-t',
            f'{user}a.pinggy.io'
        ]
        return args

    def process_output(self):
        if self.buffer.count(b'\n') == 0:
            return
        line_end = 0
        for m in re.finditer(rb'^(https?|tcp):\/*([-a-z0-9.]*)(?::([0-9]*))?\r?\n', self.buffer, re.MULTILINE | re.IGNORECASE):
            try:
                proto = m.group(1).decode('latin1')
                host = m.group(2).decode('latin1')
                port = int((m.group(3) or b'0').decode('latin1'))
                if self.poll_result is None:
                    self.poll_result = SshTunnelAddresses()
                if proto == 'http':
                    if (port == 0) or (port == 80):
                        self.poll_result.http_url = f'{proto}://{host}/'
                    else:
                        self.poll_result.http_url = f'{proto}://{host}:{port}/'
                elif proto == 'https':
                    if (port == 0) or (port == 443):
                        self.poll_result.https_url = f'{proto}://{host}/'
                    else:
                        self.poll_result.https_url = f'{proto}://{host}:{port}/'
                elif proto == 'tcp':
                    if port == 0:
                        print('TUNNEL: Invalid TCP port.')
                    else:
                        self.poll_result.tcp_address = host
                        self.poll_result.tcp_port = port
            except:
                print('TUNNEL: URL parsing error.')
            line_end = m.span()[1]
        line_end = max(line_end, self.buffer.rfind(b'\n'))
        if line_end > 0:
            self.buffer = self.buffer[line_end:]


class LocalhostRun(SshTunnelBase):

    proc: 'subprocess.Popen | None'
    buffer: bytearray
    poll_result: 'SshTunnelAddresses | None' = None

    def __init__(self, port: int=80, identity_file: 'Path | str | None'=None, ssh_path: str='ssh'):
        super().__init__(port, ssh_path)
        self.identity_file = str(identity_file) if identity_file else None

    def get_args(self):
        args = [
            self.ssh_path,
            f'-R80:localhost:{self.port}',
            '-t',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ServerAliveInterval=30',
        ]
        if self.identity_file and len(self.identity_file):
            args.append('-o')
            args.append('IdentitiesOnly=yes')
            args.append('-i')
            args.append(self.identity_file)
            args.append(f'localhost.run')
        else:
            args.append(f'nokey@localhost.run')
        return args

    def process_output(self):
        if self.buffer.count(b'\n') == 0:
            return
        line_end = 0
        for m in re.finditer(rb'([-a-z0-9.]*\.lhr\.life)', self.buffer, re.MULTILINE | re.IGNORECASE):
            if self.poll_result is None:
                self.poll_result = SshTunnelAddresses()
            host = m.group(1).decode('latin1')
            self.poll_result.https_url = f'https://{host}/'
            line_end = m.span()[1]
        line_end = max(line_end, self.buffer.rfind(b'\n'))
        if line_end > 0:
            self.buffer = self.buffer[line_end:]


if __name__ == '__main__':
    #p = Pinggy(port=8000, http=True)
    p = LocalhostRun(port=8000, identity_file='/home/doki/temp_key')
    t = time.monotonic() + 60 * 60 * 2.1
    while t > time.monotonic():
        res = p.poll()
        if res is not None:
            print(res.__dict__)
        time.sleep(0.1)
    p.exit()
