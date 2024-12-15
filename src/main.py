

import time
import lib.conf as conf
from lib.service_term import ServiceTerm
from lib.service_files import ServiceFiles
from lib.utils import poll_objects
from lib.tunnel import ConnectionType
from lib.zrok import Zrok

t = ServiceTerm()
t.setup(Zrok())
f = ServiceFiles()
f.setup(Zrok())

ssh = Zrok()
ssh.setup('ssh', ConnectionType.SSH, 22, 'dokissh', 9922)

print('===== STARTING')

t.start()
f.start()
ssh.start()
while (not t.is_started()) or (not f.is_started()) or (not ssh.is_started()):
    poll_objects()
    time.sleep(0.1)

print('===== RUNNING')

while True:
    poll_objects()
    print(t.tunnel.get_info())
    print(f.tunnel.get_info())
    print(ssh.get_info())
    time.sleep(3)
    if (conf.temp_dir / 'a').exists():
        (conf.temp_dir / 'a').rename(conf.temp_dir / 'b')
        break

print('===== STOPPING')

t.stop()
f.stop()
ssh.stop()
while (not t.is_stopped()) or (not f.is_stopped()) or (not ssh.is_stopped()):
    poll_objects()
    time.sleep(0.1)

print('===== DONE')
