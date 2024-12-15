
import lib.conf as conf
from lib.service import Service
from lib.utils import firewall_open
from lib.tunnel import ConnectionType, Tunnel


class ServiceRDP(Service):

    def setup(self, tunnel: Tunnel):
        if not conf.is_windows:
            return
        super().setup(tunnel)
        tunnel.setup('rdp', ConnectionType.TCP, conf.rdp.port, conf.rdp.endpoint, conf.rdp.client_port)
        firewall_open(conf.rdp.port)

    def start(self):
        if not conf.is_windows:
            return
        self.tunnel.start()

    def is_started(self):
        if not conf.is_windows:
            return True
        return self.tunnel.is_started()

    def stop(self):
        if not conf.is_windows:
            return
        self.tunnel.stop()

    def is_stopped(self):
        if not conf.is_windows:
            return True
        return self.tunnel.is_stopped()
