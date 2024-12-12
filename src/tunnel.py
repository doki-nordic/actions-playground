
from enum import Enum

class ConnectionType(Enum):
    HTTP = 1
    SSH = 2
    TCP = 3

class Tunnel:

    def setup(self, name: str, type: ConnectionType, port: int, endpoint: str|None, client_port: int):
        self.name = name
        self.type = type
        self.port = port
        self.endpoint = endpoint
        self.client_port = client_port

    def start(self):
        pass

    def is_started(self):
        return False

    def stop(self):
        pass

    def is_stopped(self):
        return False

    def get_info(self) -> dict[str, str]:
        # info - general info in Markdown,
        # host - optional host for client,
        # port - optional port for client,
        return { }
