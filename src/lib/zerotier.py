
from os import environ

import lib.conf as conf
from lib.tunnel import ConnectionType, Tunnel

class ZeroTier(Tunnel):

    def __init__(self):
        super().__init__()

    def setup(self, name: str, type: ConnectionType, port: int, endpoint: 'str|None', client_port: int):
        super().setup(name, type, port, endpoint, client_port)

    def start(self):
        pass

    def stop(self):
        pass

    def is_started(self):
        return True

    def is_stopped(self):
        return True

    def get_info(self) -> dict[str, str]:
        return {
            'host': environ['_PLAYGROUND_IGNORE_IP'] if '_PLAYGROUND_IGNORE_IP' in environ else conf.get_value('IP', 'unknown.host'),
            'port': self.port,
        }
