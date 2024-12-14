

import time
import lib.conf as conf
from lib.service_term import ServiceTerm
from lib.utils import poll_objects
from lib.tunnel import ConnectionType
from lib.zrok import Zrok

t = ServiceTerm()
t.setup(Zrok())

print('===== STARTING')

t.start()
while not t.is_started():
    poll_objects()
    time.sleep(0.1)

print('===== RUNNING')

while True:
    poll_objects()
    print(t.tunnel.get_info())
    time.sleep(1)
    if (conf.temp_dir / 'a').exists():
        (conf.temp_dir / 'a').rename(conf.temp_dir / 'b')
        break

print('===== STOPPING')

t.stop()
while not t.is_stopped():
    poll_objects()
    time.sleep(0.1)

print('===== DONE')
