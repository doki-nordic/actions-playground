

from tunnel import Tunnel


class Service:

    def setup(self, tunnel: Tunnel):
        self.tunnel = tunnel

    def start(self):
        pass

    def is_started(self):
        pass

    def stop(self):
        pass

    def is_stopped(self):
        pass
