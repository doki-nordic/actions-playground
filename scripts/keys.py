# Creates a set of keys needed for a new fork.
#  - SSH host key pairs: "ssh_host_*_key" and "ssh_host_*_key.pub".
#  - ZeroTier identity file: "identity.secret".
#  - Text files containing Action Secrets with newly created keys.

import subprocess
from pathlib import Path
from utils import bash_escape

parent_dir = Path(__file__).parent.parent

output = ''

for name in ('dsa', 'ecdsa', 'ed25519', 'rsa'):
    file = parent_dir / f'ssh_host_{name}_key'
    if file.exists():
        if input(f'File {file.resolve()} already exists. Override (y/n)? ') != 'y':
            exit(1)
        else:
            file.unlink()
    print(f'Generating {name} ssh key...')
    subprocess.run(['ssh-keygen', '-C', 'HostKey', '-N', '', '-t', name, '-f', file], check=True)
    text = file.read_text()
    output += f'cat > ssh_host_{name}_key <<< $\'{bash_escape(text)}\'\n'

(parent_dir / 'secrets.HOST_KEYS.txt').write_text(output)

print(f'Done ssh')

print(f'Generating ZeroTier identity key...')
identity_file = parent_dir / f'identity.secret'
if identity_file.exists():
    if input(f'File {identity_file.resolve()} already exists. Override (y/n)? ') != 'y':
        exit(1)
subprocess.run(['zerotier-idtool', 'generate', identity_file], check=True)
text = identity_file.read_text()
output = f'cat > identity.secret <<< $\'{bash_escape(text)}\'\n'
(parent_dir / 'secrets.IDENTITY.txt').write_text(output)
print(f'Done identity')
