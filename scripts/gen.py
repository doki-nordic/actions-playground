# Creates a set of keys needed for a new fork.
#  - SSH host key pairs: "ssh_host_*_key" and "ssh_host_*_key.pub".

import os
import subprocess
import pyzipper
from pathlib import Path

password = os.environ.get('PASSWORD')

if (len(password) < 1):
    print("Missing password")
    exit(1)

keys_dir = Path(__file__).parent.parent / 'keys'
keys_dir.mkdir(parents=True, exist_ok=True)

all_files: 'list[Path]' = []

# Generate host keys

for name in ('dsa', 'ecdsa', 'ed25519', 'rsa'):
    file = keys_dir / f'ssh_host_{name}_key'
    file.unlink(True)
    print(f'Generating {name} ssh key...')
    subprocess.run(['ssh-keygen', '-C', 'HostKey', '-N', '', '-t', name, '-f', file], check=True)
    all_files.append(file)
    all_files.append(file.with_suffix('.pub'))

print(f'Done ssh_host')

# Generate client key

client_key = keys_dir / 'client_key'
client_key.unlink(True)
print(f'Generating {client_key} key...')
subprocess.run(['ssh-keygen', '-C', client_key.name, '-N', '', '-t', 'ed25519', '-f', client_key], check=True)
all_files.append(client_key)
all_files.append(client_key.with_suffix('.pub'))

print(f'Done ssh_client')

# Put all to encrypted ZIP file

with pyzipper.AESZipFile(keys_dir / 'keys.zip', 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
    zf.setpassword(bytes(password, 'utf-8'))
    for file in all_files:
        zf.writestr(file.name, file.read_bytes())
    zf.writestr('localhost.run.1.txt', (keys_dir / f'ssh_host_ed25519_key.pub').read_bytes())
    zf.writestr('localhost.run.2.txt', (keys_dir / f'ssh_host_rsa_key.pub').read_bytes())

# Put client key encrypted ZIP file

with pyzipper.AESZipFile(keys_dir / 'client_key.zip', 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
    zf.setpassword(bytes(password, 'utf-8'))
    zf.writestr(client_key.name, client_key.read_bytes())
    zf.writestr('localhost.run.1.txt', (keys_dir / f'ssh_host_ed25519_key.pub').read_bytes())
    zf.writestr('localhost.run.2.txt', (keys_dir / f'ssh_host_rsa_key.pub').read_bytes())


for file in all_files:
    file.unlink()
