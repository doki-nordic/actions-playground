
import os
import sys
import pyzipper
import subprocess
from pathlib import Path

print('START')

this_dir = Path(__file__).parent
parent_dir = this_dir.parent

password = os.environ.get('PASSWORD')

print(f'PASS: ${password}')

if password is None:
    print('Please provide a password for the script in PASSWORD action secret (or environment variable if running locally).')
    exit(1)

client_count = int(sys.argv[1]) if len(sys.argv) > 1 else 1

print(f'PASS: ${client_count}')

subprocess.run([sys.executable, this_dir / 'keys.py'], check=True)
print(f'DONE')
for i in range(client_count):
    subprocess.run([sys.executable, this_dir / 'client_key.py'], check=True)
    print(f'DONE')

with pyzipper.AESZipFile(parent_dir / 'keys.zip', 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
    zf.setpassword(bytes(password, 'utf-8'))
    for name in ('secrets.CLIENT_KEYS.txt',
                 'secrets.HOST_KEYS.txt',
                 'secrets.IDENTITY.txt',
                 'ssh_host_dsa_key',
                 'ssh_host_dsa_key.pub',
                 'ssh_host_ecdsa_key',
                 'ssh_host_ecdsa_key.pub',
                 'ssh_host_ed25519_key',
                 'ssh_host_ed25519_key.pub',
                 'ssh_host_rsa_key',
                 'ssh_host_rsa_key.pub',
                 'identity.secret'):
        zf.writestr(name, (parent_dir / name).read_text())
        print(f'ADDED {name}')
    for name in parent_dir.iterdir():
        if (name.name == 'client_key') or (name.name == 'client_key.pub'):
            zf.writestr(name.name, (parent_dir / name).read_text())
            print(f'ADDED {name}')
        if name.name.startswith('client_key_') and name.suffix == '.pub':
            zf.writestr(name.name, (parent_dir / name).read_text())
            print(f'ADDED {name}')
        if name.name.startswith('client_key_') and name.suffix == '':
            zf.writestr(name.name, (parent_dir / name).read_text())
            print(f'ADDED {name}')

