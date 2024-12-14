
import os
import time
import signal
import subprocess
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

import lib.conf as conf
from lib.utils import add_polling_object, delete_polling_object, poll_objects


def interrupt_process(process: subprocess.Popen):
    os.killpg(process.pid, signal.SIGINT)


def windows_compatibility():
    import win32pipe, win32file, win32console # type: ignore
    def interrupt_process(process: subprocess.Popen):
        win32console.GenerateConsoleCtrlEvent(win32console.CTRL_BREAK_EVENT, process.pid)
    return (interrupt_process,)

if conf.is_windows:
    (interrupt_process,) = windows_compatibility()

class State(Enum):
    RUNNING = 1
    INTERRUPTING = 2 # SIGINT send and waiting (or CTRL_BREAK_EVENT on Windows)
    TERMINATING = 3 # terminate() called and waiting
    KILLING = 4 # kill() called and waiting
    STOPPED = 5 # process is stopped


def read_pipe(file):
    try:
        return file.read1()
    except:
        return None


class ProcessHandler:

    def __init__(self, *args, **kwargs):
        self.state = State.RUNNING
        self.on_exit = None
        self.on_stdout = None
        self.timeout = 3
        print(f'Executing (by {id(self)})', args[0] if len(args) > 1 else (kwargs['args'] if 'args' in kwargs else ''))
        if not conf.is_windows:
            kwargs['preexec_fn'] = os.setpgrp
        self.processes = subprocess.Popen(*args, **kwargs)
        print(f'    pid (by {id(self)})', self.processes.pid)
        self.terminate_time = 0
        if ('stdout' in kwargs) and (kwargs['stdout'] == subprocess.PIPE):
            self.executor = ThreadPoolExecutor(1)
        else:
            self.executor = None
        self.future = None
        add_polling_object(self)

    def terminate(self, timeout: int):
        if self.state == State.RUNNING:
            self.state = State.INTERRUPTING
            self.timeout = timeout
            self.terminate_time = time.time() + timeout
            print(f'Interrupt {self.processes.pid}')
            interrupt_process(self.processes)

    def is_terminated(self):
        return (self.state == State.STOPPED)

    def _terminated(self):
        print(f'Terminated {self.processes.pid} with exit code', self.processes.returncode)
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
        if self.on_exit is not None:
            self.on_exit(self.processes, self.state != State.RUNNING)
        self.state = State.STOPPED
        self.processes = None
        delete_polling_object(self)

    def poll(self):
        if self.state == State.STOPPED:
            delete_polling_object(self)
            return
        if self.processes.poll() is not None:
            self._terminated()
            return
        if (self.state != State.RUNNING) and (time.time() >= self.terminate_time):
            if self.state == State.INTERRUPTING:
                print(f'Interrupting failed, trying to terminate {self.processes.pid}')
                self.terminate_time = time.time() + self.timeout
                self.processes.terminate()
                self.state = State.TERMINATING
            elif self.state == State.TERMINATING:
                print(f'Terminating failed, trying to kill {self.processes.pid}')
                self.terminate_time = time.time() + 3
                self.processes.kill()
                self.state = State.KILLING
            elif self.state == State.KILLING:
                print(f'Killing failed, cannot stop {self.processes.pid}')
                self._terminated()
        if self.executor:
            if not self.future:
                self.future = self.executor.submit(read_pipe, self.processes.stdout)
            if self.future.done():
                output = self.future.result()
                self.future = self.executor.submit(read_pipe, self.processes.stdout)
                if (output is not None) and (len(output) > 0) and self.on_stdout:
                    self.on_stdout(output)

def run_ret(*args, **kwargs):
    kwargs['stdout'] = subprocess.PIPE
    kwargs['stderr'] = subprocess.PIPE
    result = subprocess.run(*args, **kwargs)
    stdout = str(result.stdout, 'utf-8')
    stderr = str(result.stderr, 'utf-8')
    return (stdout, stderr, result.returncode)

def _test_handler():

    terminate_timeout = 10

    def on_exit(proc: subprocess.Popen, forced: bool):
        nonlocal exited
        print(f'-- Exited with {proc.returncode} {"forced" if forced else "normally"}')
        exited = True

    def on_stdout(data: bytes):
        nonlocal buffer, ph
        buffer += data
        text = str(buffer, 'utf-8')
        print('-- STDOUT:', text)
        if text.find('Second line') >= 0:
            ph.terminate(terminate_timeout)

    file = conf.temp_dir / 'tmp.sh'
    file.write_text('''#!/bin/bash
                    echo "First line"
                    sleep 3
                    echo "Second line"
                    sleep 3
                    echo "Finish"
                    ''')
    file.chmod(0o777)

    print('-------------- SIMPLE RUN')

    ph = ProcessHandler(['/bin/bash', str(file)])
    exited = False
    ph.on_exit = on_exit
    while not exited:
        poll_objects()
        time.sleep(0.1)

    print('-------------- INTERRUPT')

    for i in range(2):

        ph = ProcessHandler(['/bin/bash', str(file)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
        exited = False
        buffer = b''
        ph.on_exit = on_exit
        ph.on_stdout = on_stdout
        while not exited:
            poll_objects()
            time.sleep(0.1)

        file = conf.temp_dir / 'tmp.sh'
        file.write_text('''#!/bin/bash
                        trap 'echo "Ctrl-C ignored"' SIGINT
                        echo "First line"
                        sleep 3
                        echo "Second line"
                        sleep 3
                        echo "Finish"
                        sleep 5
                        ''')
        file.chmod(0o777)

        print('-------------- IGNORED INTERRUPT')

    print('-------------- WITH TIMEOUT')

    ph = ProcessHandler(['/bin/bash', str(file)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
    exited = False
    buffer = b''
    ph.on_exit = on_exit
    ph.on_stdout = on_stdout
    terminate_timeout = 1
    while not exited:
        poll_objects()
        time.sleep(0.1)

    print('-- Tests done')
    file.unlink()

if __name__ == "__main__":
    _test_handler()
