
import lib.ssh_keygen as ssh_keygen

from pathlib import Path

def save_key(name, key, private=False):
    path: Path = Path(__file__).parent.parent.parent / '_tmp' / name
    with open(path, 'w') as f:
        f.write(key)
    if private:
        path.chmod(0o600)

(rsa_private, rsa_public) = ssh_keygen.generate_rsa('123', 'HostKey', 2048)
save_key('ssh_host_rsa_key', rsa_private, True)
save_key('ssh_host_rsa_key.pub', rsa_public)

(ed25519_private, ed25519_public) = ssh_keygen.generate_ed25519('123', 'HostKey')
save_key('ssh_host_ed25519_key', ed25519_private, True)
save_key('ssh_host_ed25519_key.pub', ed25519_public)

(ecdsa_private, ecdsa_public) = ssh_keygen.generate_ecdsa('123', 'HostKey', ssh_keygen.ec.SECP256R1())
save_key('ssh_host_ecdsa_key', ecdsa_private, True)
save_key('ssh_host_ecdsa_key.pub', ecdsa_public)

(dsa_private, dsa_public) = ssh_keygen.generate_dsa('123', 'HostKey', 1024)
save_key('ssh_host_dsa_key', dsa_private, True)
save_key('ssh_host_dsa_key.pub', dsa_public)
