
import json
import shutil
import sys
import time
import jinja2
import re
import inputs
import subprocess
import getpass
import pyzipper
from os import SEEK_END
from pathlib import Path
from ssh_tunnel import LocalhostRun, Pinggy
from textwrap import dedent

SKIP_ENV_VARS = r'_|!.:|PWD'

def unpack_zip():
    with pyzipper.AESZipFile(inputs.keys_dir / 'keys.zip') as zf:
        zf.setpassword(bytes(inputs.contexts['secrets']['PASSWORD'], 'utf-8'))
        zf.extractall(inputs.keys_dir)

def render_template(input: Path, output: Path):
    env = jinja2.Environment()
    env.filters['posix'] = inputs.posix_path
    tmpl = env.from_string(input.read_text())
    data = dict(inputs.__dict__)
    if output.exists():
        data['old'] = output.read_text()
    text = tmpl.render(**data)
    output.write_text(text)
    return output

def render_templates():
    shutil.copy(inputs.data_dir / 'bash_history', Path.home() / '.bash_history')
    render_template(inputs.data_dir / 'bashrc.jinja', Path.home() / '.bashrc')
    render_template(inputs.data_dir / 'bash_profile.jinja', Path.home() / '.bash_profile')
    render_template(inputs.data_dir / 'sshd.conf.jinja', inputs.keys_dir / 'sshd.conf')

def render_root_templates():
    render_template(inputs.data_dir / 'exit_job.jinja', inputs.bin_dir / 'exit_job').chmod(0o755)
    if inputs.windows:
        render_template(inputs.data_dir / 'exit_job.bat.jinja', inputs.bin_dir / 'exit_job.bat')
    render_template(inputs.data_dir / 'ghctx.jinja', inputs.bin_dir / 'ghctx').chmod(0o755)
    if inputs.windows:
        render_template(inputs.data_dir / 'ghctx.bat.jinja', inputs.bin_dir / 'ghctx.bat')
    render_template(inputs.data_dir / 'ghactionplaygr_tool.jinja', inputs.bin_dir / 'ghactionplaygr_tool').chmod(0o755)

def write_client_keys():
    keys = inputs.contexts['secrets']['CLIENT_KEY']
    keys += '\n' + (inputs.keys_dir / 'client_key.pub').read_text()
    keys = re.sub(f'(?:\\s*[\\r\\n])+\\s*', '\n', keys.strip()) + '\n'
    (inputs.keys_dir / 'authorized_keys').write_text(keys)

def get_sshd_path():
    result = subprocess.run(['which', 'sshd'], stdout=subprocess.PIPE, check=True)
    return str(result.stdout, 'utf-8').rstrip()

def run_sshd_server():
    exit_file = inputs.temp_dir / 'exit_job_file'
    pid_file = inputs.keys_dir / 'sshd_pid'
    exit_file.unlink(True)
    try:
        pid_file.unlink(True)
    except:
        pass
    sshd_path = get_sshd_path()
    print('sshd binary', sshd_path)
    args = [sshd_path, '-D', '-f', str(inputs.keys_dir / 'sshd.conf')]
    print('Executing', args)
    sshd_process = subprocess.Popen(args)
    print('sshd pid', sshd_process.pid)
    while True:
        if sshd_process.poll() is not None:
            print(f'sshd terminated with exit code {sshd_process.returncode}')
            exit(sshd_process.returncode)
        if exit_file.exists():
            break
        poll_tunnels()
        time.sleep(0.5)
    exit_tunnels()
    sshd_process.terminate()
    try:
        sshd_process.wait(15)
    except:
        print('Wait timeout after SIGTERM')
        if sshd_process.returncode is None:
            sshd_process.kill()
            sshd_process.wait(3)
    print('sshd exit code', sshd_process.returncode)
    time.sleep(15)

def set_permissions():
    for file in inputs.keys_dir.glob('ssh_host_*'):
        file.chmod(0o600)
    (inputs.keys_dir / 'authorized_keys').chmod(0o600)
    (inputs.temp_dir / "artifact").mkdir(exist_ok=True)

def stop_ssh_service():
    stop_cmd = (['launchctl', 'unload', '/System/Library/LaunchDaemons/ssh.plist']
                if inputs.macos else
                ['systemctl', 'stop', 'ssh'])
    check_cmd = ['netstat', '-anvp', 'tcp'] if inputs.macos else ['netstat', '-lt']
    check_re = r'\.22\s' if inputs.macos else r':(22|ssh)\s'
    subprocess.run(stop_cmd)
    for _ in range(15):
        time.sleep(1)
        result = subprocess.run(check_cmd, stdout=subprocess.PIPE, check=True)
        port_list = str(result.stdout, 'utf-8')
        if re.search(check_re, port_list) is None:
            break

def start_sshd_service():
    exit_file = inputs.temp_dir / 'exit_job_file'
    try:
        exit_file.unlink()
    except:
        pass
    user_ssh_dir = Path.home() / '.ssh'
    global_ssh_dir = Path(r'c:\ProgramData\ssh')
    user_ssh_dir.mkdir(exist_ok=True)
    banner_name = 'banner-bash.txt' if inputs.contexts['github']['event']['inputs']['os'] == 'bash' else 'banner-cmd.txt'
    shutil.copy(inputs.keys_dir / 'authorized_keys', user_ssh_dir / 'authorized_keys')
    shutil.copy(inputs.keys_dir / 'authorized_keys', global_ssh_dir / 'administrators_authorized_keys')
    shutil.copy(inputs.data_dir / banner_name, global_ssh_dir / banner_name)
    for dest_file in global_ssh_dir.glob('ssh_host_*_key*'):
        src_file = inputs.keys_dir / dest_file.name
        with open(dest_file, 'rb+') as dst:
            dst.truncate(0)
            dst.write(src_file.read_bytes())
    sshd_conf = global_ssh_dir / 'sshd_config'
    with open(sshd_conf, 'rb+') as fd:
        fd.seek(0, SEEK_END)
        fd.write(b'\r\n')
        fd.write(bytes(f'Banner __PROGRAMDATA__/ssh/{banner_name}\r\n', 'utf-8'))
    subprocess.run(['net', 'start', 'sshd'], check=True)
    while True:
        if exit_file.exists():
            break
        poll_tunnels()
        time.sleep(0.5)
    exit_tunnels()

def allow_low_ports():
    if inputs.ubuntu:
        sshd_path = get_sshd_path()
        subprocess.run(['setcap', 'cap_net_bind_service=+ep', sshd_path], check=True)
        subprocess.run(['setcap', 'cap_net_bind_service=+ep', str(inputs.temp_dir / 'ttyd')], check=True)

def bash_escape(text):
    return re.sub(r'[^ /0-9a-zA-Z_+:;,.=\-]', lambda m: '\\n' if m.group(0) == '\n' else f'\\x{ord(m.group(0)):02x}', text)

def bat_escape(text):
    return (text
        .replace('%', '%%')
        .replace('^', '^^')
        .replace('&', '^&')
        .replace('<', '^<')
        .replace('>', '^>')
        .replace('|', '^|')
        .replace('\'', '^\'')
        .replace('`', '^`')
        .replace(',', '^,')
        .replace(';', '^;')
        .replace('=', '^=')
        .replace('(', '^(')
        .replace(')', '^)')
        .replace('"', '^"')
        .replace('\r\n', '\n')
        .replace('\n', '^\r\n\r\n')
        )

def write_bash_env():
    src = inputs.temp_dir / 'bash_env.txt'
    output = [ '#!/bin/bash' ]
    for line in src.read_text().split('\n'):
        line = line.rstrip('\r')
        pos = line.find('=')
        if pos < 0:
            continue
        name = line[:pos]
        value = line[pos + 1:]
        if re.fullmatch(r'[A-Z_a-z][0-9A-Z_a-z]*', name) and not re.fullmatch(SKIP_ENV_VARS, name, re.IGNORECASE):
            output.append(f'export {name}=$\'{bash_escape(value)}\'')
    output.append(f'export GH_ARTIFACT={inputs.posix_path(inputs.temp_dir / "artifact")}')
    output.append(f'cd {inputs.posix_path(inputs.contexts["github"]["workspace"])}')
    dst = inputs.bin_dir / 'load_job'
    dst.write_text('\n'.join(output) + '\n')
    dst.chmod(0o755)

def write_bat_env():
    src = inputs.temp_dir / 'cmd_env.json'
    if not src.exists():
        return
    src = json.loads(src.read_text())
    output = [ '@echo off' ]
    for name, value in src.items():
        if not re.fullmatch(SKIP_ENV_VARS, name, re.IGNORECASE):
            output.append(f'set {name}={bat_escape(value)}')
    output.append(f'set GH_ARTIFACT={str(inputs.temp_dir / "artifact")}')
    output.append(f'cd /d "{inputs.contexts["github"]["workspace"]}"')
    dst = inputs.bin_dir / 'load_job.bat'
    dst.write_text('\r\n'.join(output) + '\r\n')

ttyd_tunnel = None
ssh_tunnel = None
desktop_tunnel = None
files_tunnel = None
files_tunnel2 = None

info_ttyd_url = None
info_ssh_address = None
info_ssh_port = None
info_desktop_address = None
info_desktop_port = None
info_files_url = None

def start_tunnels():
    global ttyd_tunnel, ssh_tunnel, desktop_tunnel, files_tunnel, files_tunnel2
    print('Starting tunnels')
    ttyd_tunnel = LocalhostRun(port=80, identity_file=inputs.keys_dir / 'ssh_host_ed25519_key')
    pinggy_token = None
    if 'PINGGY_TOKEN' in inputs.contexts['secrets']:
        pinggy_token = inputs.contexts['secrets']['PINGGY_TOKEN'].strip()
    ssh_tunnel = Pinggy(port=22, http=False, token=pinggy_token)
    if inputs.windows:
        desktop_tunnel = Pinggy(port=3389, http=False, token=pinggy_token)
    elif inputs.macos:
        desktop_tunnel = Pinggy(port=5900, http=False, token=pinggy_token)
    else:
        desktop_tunnel = None
    files_tunnel = LocalhostRun(port=8080, identity_file=inputs.keys_dir / 'ssh_host_rsa_key')
    files_tunnel2 = Pinggy(port=8080, http=True, token=pinggy_token)
    print('Done starting tunnels')
    sys.stdout.flush()

def poll_tunnels():
    global ttyd_tunnel, ssh_tunnel, desktop_tunnel, files_tunnel, files_tunnel2
    global info_ttyd_url, info_ssh_address, info_ssh_port, info_desktop_address, info_desktop_port, info_files_url
    update_info = False
    res = ttyd_tunnel.poll()
    if res and res.https_url:
        info_ttyd_url = res.https_url
        update_info = True
    res = ssh_tunnel.poll()
    if res and res.tcp_address:
        info_ssh_address = res.tcp_address
        info_ssh_port = res.tcp_port
        update_info = True
    if desktop_tunnel:
        res = desktop_tunnel.poll()
        if res and res.tcp_address:
            info_desktop_address = res.tcp_address
            info_desktop_port = res.tcp_port
            update_info = True
    res = files_tunnel.poll()
    if res and res.https_url:
        info_files_url = res.https_url
        update_info = True
    res = files_tunnel2.poll()
    if res and res.https_url:
        info_files_url = res.https_url
        update_info = True
    if update_info:
        update_connection_info()

def exit_tunnels():
    global ttyd_tunnel, ssh_tunnel, desktop_tunnel, files_tunnel, files_tunnel2
    if ttyd_tunnel:
        ttyd_tunnel.exit()
    if ssh_tunnel:
        ssh_tunnel.exit()
    if desktop_tunnel:
        desktop_tunnel.exit()
    if files_tunnel:
        files_tunnel.exit()
    if files_tunnel2:
        files_tunnel.exit()

def update_connection_info():
    global info_ttyd_url, info_ssh_address, info_ssh_port, info_desktop_address, info_desktop_port, info_files_url
    user = getpass.getuser()
    info = ''
    if info_ttyd_url:
        info += dedent(f'''
            ### HTTP Shell\n
            &nbsp; | [{info_ttyd_url}]({info_ttyd_url})
            --|--
            User name | `{user}`
            ''')
    if info_files_url:
        info += dedent(f'''
            ### HTTP File Browser\n
            &nbsp;    | [{info_files_url}]({info_files_url})
            ----------|--
            User name | `{user}`
            ''')
    if info_ssh_address:
        url_port = '' if info_ssh_port == 22 else f':{info_ssh_port}'
        cmd_port = '' if info_ssh_port == 22 else f'-p {info_ssh_port} '
        info += dedent(f'''
            ### SSH/SFTP\n
            &nbsp;  | [ssh://{user}@{info_ssh_address}{url_port}](https://doki-nordic.github.io/actions-playground/redir.html#ssh://{user}@{info_ssh_address}{url_port})
            --------|--
            &nbsp;  | [sftp://{user}@{info_ssh_address}{url_port}](https://doki-nordic.github.io/actions-playground/redir.html#sftp://{user}@{info_ssh_address}{url_port})
            Address | `{info_ssh_address}`
            Port    | `{info_ssh_port}{'' if url_port else ' (default)'}`
            User    | `{user}`
            Command | `ssh {cmd_port}{user}@{info_ssh_address}`
            ''')
    if info_desktop_address:
        info += '\n```\n'
        if inputs.windows:
            info += f'RDP:   address: {info_desktop_address}\n'
            info += f'RDP:   port:    {info_desktop_port}\n'
            info += f'RDP:   user:    {user}\n'
            info += f'RDP:   rdp://full%20address=s:{info_desktop_address}:{info_desktop_port}&username=s:{user}\n'
            info += f'RDP:   ms-rd://full%20address=s:{info_desktop_address}:{info_desktop_port}&username=s:{user}\n'
        elif inputs.macos:
            info += f'VNC:   address: {info_desktop_address}\n'
            info += f'VNC:   port:    {info_desktop_port}\n'
            info += f'VNC:   user:    {user}\n'
            info += f'VNC:   vnc://{info_desktop_address}:{info_desktop_port}\n'
        info += '```\n'
    print(info)
    sys.stdout.flush()
    markdown_file = inputs.wiki_dir / (str(inputs.contexts['github']['run_id']) + '.md')
    markdown_file.write_text(info)
    git = shutil.which('git')
    subprocess.run([git, 'add', '.'], shell=False, check=True, cwd=str(inputs.wiki_dir))
    subprocess.run([git, 'commit', '-m', f'Add {inputs.contexts["github"]["run_id"]} run page'], shell=False, check=True, cwd=str(inputs.wiki_dir))
    subprocess.run([git, 'push', 'origin'], shell=False, check=True, cwd=str(inputs.wiki_dir))

if __name__ == '__main__':
    if sys.argv.count('--as-root'):
        if not inputs.windows:
            stop_ssh_service()
        allow_low_ports()
        render_root_templates()
        write_bash_env()
        write_bat_env()
    else:
        unpack_zip()
        render_templates()
        write_client_keys()
        set_permissions()
        start_tunnels()
        if inputs.windows:
            start_sshd_service()
        else:
            run_sshd_server()
