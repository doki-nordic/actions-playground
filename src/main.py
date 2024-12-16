
import time
import lib.conf as conf
from lib.service_term import ServiceTerm
from lib.service_files import ServiceFiles
from lib.utils import poll_objects
from lib.tunnel import ConnectionType
from lib.zrok import Zrok
from lib.bore import Bore
from lib.zerotier import ZeroTier
from lib.service import Service
from lib.service_rdp import ServiceRDP
from lib.service_ssh import ServiceSSH

services: 'list[Service]' = []

t = ServiceTerm()
t.setup(ZeroTier())
services.append(t)

f = ServiceFiles()
f.setup(ZeroTier())
services.append(f)

rdp = ServiceRDP()
rdp.setup(ZeroTier())
services.append(rdp)

ssh = ServiceSSH()
ssh.setup(ZeroTier())
services.append(ssh)


print('===== STARTING')

for service in services:
    service.start()
while [True for service in services if not service.is_started()]:
    poll_objects()
    time.sleep(0.1)

print('===== RUNNING')

while True:
    poll_objects()
    for service in services:
        if hasattr(service, 'tunnel'):
            print(service.tunnel.get_info())
        elif hasattr(service, 'get_info'):
            print(service.get_info())
    time.sleep(3)
    if (conf.temp_dir / 'a').exists():
        (conf.temp_dir / 'a').rename(conf.temp_dir / 'b')
        break

print('===== STOPPING')

for service in services:
    service.stop()
while [True for service in services if not service.is_stopped()]:
    poll_objects()
    time.sleep(0.1)

print('===== DONE')
