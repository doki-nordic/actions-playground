
import os
import sys
import time
import json
import shutil
import pickle
import random
import tarfile
import zipfile
import threading
import subprocess
import urllib.request
from pathlib import Path
from typing import Literal

import lib.conf as conf
import lib.ctx as ctx

def download(url: str, output: 'Path|None') -> bytes:
    urllib.request.urlretrieve(url, output)


def untar(file: Path, output: Path, compression: 'Literal["gz", "xz", "bz2"]|None') -> None:
    with tarfile.open(file, 'r' if compression is None else 'r:' + compression) as tar:
        tar.extractall(path=output)

def unzip(file: Path, output: Path) -> None:
    with zipfile.ZipFile(file, 'r') as zf:
        zf.extractall(output)


polling_objects = set()


def add_polling_object(obj):
    polling_objects.add(obj)


def delete_polling_object(obj):
    polling_objects.discard(obj)


def poll_objects():
    for obj in [*polling_objects]:
        if hasattr(obj, 'poll'):
            obj.poll()
        else:
            obj()


_pickle_counter = 0
_pickle_file_name = ''.join(random.choices('1234567890qwertyuiopasdfghjklzxcvbnm', k=12))


def _run_cleanup(*args, **kwargs):
    retry = [1, 0]
    if 'retry' in kwargs:
        retry = kwargs['retry']
        del kwargs['retry']
    for i in range(retry[0]):
        if i > 0:
            time.sleep(retry[1])
        try:
            ret = subprocess.run(*args, **kwargs)
            if ret.returncode == 0:
                return
        except:
            pass


def prepare_remote_call(function, args, kwargs, extension = 'pickle') -> Path:
    global _pickle_counter
    _pickle_counter += 1
    pickle_file = conf.temp_dir / (_pickle_file_name + str(_pickle_counter) + '.' + extension)
    script_file = function.__globals__['__file__']
    with open(pickle_file, "wb") as fd:
        pickle.dump({
            'file': script_file,
            'func': function.__name__,
            'args': args,
            'kwargs': kwargs,
        }, fd)
    return pickle_file


def remote_call_result(pickle_file):
    with open(pickle_file, "rb") as fd:
        loaded_data = pickle.load(fd)
    pickle_file.unlink()
    if 'ex' in loaded_data:
        raise loaded_data['ex']
    elif 'ret' in loaded_data:
        return loaded_data['ret']
    else:
        raise Exception('No return value or exception')


def as_root(function, *args, **kwargs):
    if (not hasattr(os, 'geteuid')) or (os.geteuid() == 0):
        return function(*args, **kwargs)
    pickle_file = prepare_remote_call(function, args, kwargs)
    subprocess.run([shutil.which('sudo'), sys.executable, conf.scripts_dir / 'do_remote_call.py', pickle_file], check=True)
    return remote_call_result(pickle_file)


def add_cleanup_function(order: int, function, *args, **kwargs) -> Path:
    return prepare_remote_call(function, args, kwargs, f'{order}.cleanup')


def add_cleanup_command(order: int, *args, **kwargs) -> Path:
    return add_cleanup_function(order, _run_cleanup, *args, **kwargs)


class CallOnce:

    def __init__(self):
        self.event = threading.Event()
        self.lock = threading.Lock()
        self.result = None
        self.exception = None

    def call(self, callback, *args, **kwargs):
        if not self.event.is_set():
            with self.lock:
                if not self.event.is_set():
                    try:
                        self.result = callback(*args, **kwargs)
                    except Exception as ex:
                        self.exception = ex
                    finally:
                        self.event.set()
        if self.exception is not None:
            raise self.exception
        return self.result


def firewall_open(port: int, program: 'str|None' = None):
    if conf.is_windows:
        if port == 80:
            subprocess.run([shutil.which('net'), 'stop', '/y', 'W3SVC'])
        subprocess.run([
            shutil.which('netsh'), 'advfirewall',
            'firewall', 'add', 'rule',
            f'name=OpenPort{port}', 'dir=in', 'action=allow', 'protocol=TCP',
            f'localport={port}'
        ], check=True, shell=False)
    elif conf.is_linux:
        #subprocess.run(['ufw', 'allow', str(port)], check=True, shell=True)
        if program:
            subprocess.run([conf.sudo, 'setcap', 'cap_net_bind_service=+ep', str(Path(program).resolve())], check=True)
    # elif conf.is_macos:
    #     subprocess.run(['brew', 'services', 'start', 'firewall', '--args', 'add', 'port', str(port), 'tcp'])


def get_environment(pwd):
    json_file = conf.temp_dir / (ctx.inputs.shell + '.json')
    with open(json_file, 'rb') as fd:
        env = json.load(fd)
    for name in [*env.keys()]:
        if name.startswith('_PLAYGROUND_IGNORE_'):
            del env[name]
        elif name == 'PWD':
            env[name] = str(pwd)
        elif name.startswith('GITHUB_'):
            env[name] = os.getenv(name, env[name])
    return env


global_unpack_once = CallOnce()


def unpack_keys(_checked=False):
    if not _checked:
        return global_unpack_once.call(unpack_keys, True)
    import pyzipper
    with pyzipper.AESZipFile(conf.keys_dir / 'keys.zip') as zf:
        zf.setpassword(bytes(ctx.secrets.PASSWORD, 'utf-8'))
        zf.extractall(conf.keys_dir)
