from pyre import Pyre
from pyre import zhelper
import threading
import zmq
import logging
import json
import time

from uniflex.core import modules

__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2015, Technische Universitat Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz}@tkn.tu-berlin.de"


class PyreDiscoveryMasterModule(modules.ControlApplication):
    def __init__(self, iface, groupName="uniflex", downlink=None, sub=None,
                 uplink=None, pub=None):
        super(PyreDiscoveryMasterModule, self).__init__()
        self.log = logging.getLogger('pyre_discovery_module.main')

        pyreLogger = logging.getLogger('pyre')
        pyreLogger.setLevel(logging.CRITICAL)

        self.running = False
        self.iface = iface
        self.sub = downlink
        if not self.sub:
            self.sub = sub
        self.pub = uplink
        if not self.pub:
            self.pub = pub
        self.groupName = groupName
        self.ctx = zmq.Context()

    def _sending_announcements(self):
        while self.running:
            self.log.debug("Discovery Announcements:"
                           " SUB={}, PUB={}"
                           .format(self.sub, self.pub))

            msg = json.dumps({'downlink': self.sub,
                              'uplink': self.pub})
            self.discovery_pipe.send(msg.encode('utf_8'))
            time.sleep(2)

    @modules.on_start()
    def start_discovery_announcements(self):
        self.log.debug("Start discovery announcements".format())
        self.running = True
        self.discovery_pipe = zhelper.zthread_fork(
            self.ctx, self.discovery_task)

        d = threading.Thread(target=self._sending_announcements)
        d.setDaemon(True)
        d.start()
        return True

    @modules.on_exit()
    def stop_discovery_announcements(self):
        self.log.debug("Stop discovery announcements".format())
        if self.running:
            self.running = False
            self.discovery_pipe.send("$$STOP".encode('utf_8'))

    def discovery_task(self, ctx, pipe):
        self.log.debug("Pyre on iface : {}".format(self.iface))
        n = Pyre(self.groupName, sel_iface=self.iface)
        n.set_header("DISCOVERY_Header1", "DISCOVERY_HEADER")
        n.join(self.groupName)
        n.start()

        poller = zmq.Poller()
        poller.register(pipe, zmq.POLLIN)

        while(True):
            items = dict(poller.poll())

            if pipe in items and items[pipe] == zmq.POLLIN:
                message = pipe.recv()
                # message to quit
                if message.decode('utf-8') == "$$STOP":
                    break

                n.shout(self.groupName, message)

        n.stop()
