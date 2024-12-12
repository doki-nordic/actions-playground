
import os
import threading
import pickle
from os import PathLike
import random
import sys
import urllib.request
import tarfile
import conf
from pathlib import Path
from typing import Literal

def download(url: str, output: 'Path|None') -> bytes:
    urllib.request.urlretrieve(url, output)

def untar(file: Path, output: Path, compression: Literal['gz', 'xz', 'bz2']|None) -> None:
    with tarfile.open(file, 'r' if compression is None else 'r:' + compression) as tar:
        tar.extractall(path=output)

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

def add_cleanup_command(priority: int, *args, **kwargs):
    add_cleanup_script(priority, conf.scripts_dir / 'proc.py', *args, **kwargs) # TODO: proc.py replaced by __file__

_script_counter = 0
_celanup_file_name = ''.join(random.choices('1234567890qwertyuiopasdfghjklzxcvbnm', k=16))

def add_cleanup_script(priority: int, file: PathLike[str], *args, **kwargs):
    global _script_counter
    _script_counter += 1
    pickle_file = conf.temp_dir / (_celanup_file_name + str(_script_counter) + '.cleanup')
    with open(pickle_file, "wb") as fd:
        pickle.dump({
            'priority': priority,
            'file': file,
            'args': args,
            'kwargs': kwargs,
        }, fd) # TODO: return token (or object) that can be used to remove this cleanup

def call_cleanup_script(callback):
    if (len(sys.argv) == 3) and (sys.argv[1] == '_do_cleanup_'):
        try:
            with open(sys.argv[2], "rb") as fd:
                loaded_data = pickle.load(fd)
            callback(*loaded_data['args'], **loaded_data['kwargs'])
        finally:
            Path(sys.argv[2]).unlink()
        sys.exit(0)

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
