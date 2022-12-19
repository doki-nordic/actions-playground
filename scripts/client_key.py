# Creates a new client ssh key pair: "client_key" and "client_key.pub".
# If files already exists, appends a number to file names.
# Public key is appended to "secrets.CLIENT_KEYS.txt" file.

import subprocess
from pathlib import Path

parent_dir = Path(__file__).parent.parent

file = parent_dir / 'client_key'
n = 1
while file.exists():
    n += 1
    file = parent_dir / f'client_key_{n}'
print(f'Generating {file} key...')
subprocess.run(['ssh-keygen', '-C', file.name, '-N', '', '-t', 'ed25519', '-f', file], check=True)
pub_file = file.with_suffix('.pub')
text = pub_file.read_text()

output_file = parent_dir / 'secrets.CLIENT_KEYS.txt'
with open(output_file, 'a') as f:
    f.write(text)
    if not text.endswith('\n'):
        f.write('\n')
