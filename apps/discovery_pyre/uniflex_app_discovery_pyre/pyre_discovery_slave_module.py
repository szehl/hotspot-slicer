from pyre import Pyre
from pyre import zhelper
import threading
import zmq
import uuid
import logging
import json
import time

from uniflex.core import modules
from uniflex.core import events

__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2015, Technische Universitat Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz}@tkn.tu-berlin.de"


class PyreDiscoverySlaveModule(modules.ControlApplication):
    def __init__(self, iface, groupName="uniflex"):
        super(PyreDiscoverySlaveModule, self).__init__()
        self.log = logging.getLogger('pyre_discovery_module.main')

        pyreLogger = logging.getLogger('pyre')
        pyreLogger.setLevel(logging.CRITICAL)

        self.running = False
        self.iface = iface
        self.controller_dl = None
        self.controller_ul = None
        self.groupName = groupName
        self.discovery_pipe = None
        self.ctx = zmq.Context()

    def _receive_announcements(self):
        while self.running:
            # self.log.debug("Discovery procedure running".format())
            time.sleep(2)

    @modules.on_start()
    @modules.on_disconnected()
    def start_discovery(self):
        if self.running:
            return
        self.log.debug("Start discovery procedure".format())

        self.running = True
        self.controller_dl = None
        self.controller_ul = None

        self.discovery_pipe = zhelper.zthread_fork(
            self.ctx, self.discovery_task)

        d = threading.Thread(target=self._receive_announcements)
        d.setDaemon(True)
        d.start()
        return True

    @modules.on_exit()
    @modules.on_connected()
    def stop_discovery(self):
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
        poller.register(n.inbox, zmq.POLLIN)

        while(True):
            items = dict(poller.poll())

            if pipe in items and items[pipe] == zmq.POLLIN:
                message = pipe.recv()
                # message to quit
                if message.decode('utf-8') == "$$STOP":
                    break

            if n.inbox in items and items[n.inbox] == zmq.POLLIN:
                cmds = n.recv()
                self.log.debug("NODE_MSG CONT:{}".format(cmds))

                msg_type = cmds.pop(0)
                peer_uuid_bytes = cmds.pop(0)
                peer_uuid = uuid.UUID(bytes=peer_uuid_bytes)

                self.log.debug("NODE_MSG TYPE: {}".format(msg_type))
                self.log.debug("NODE_MSG PEER: {}".format(peer_uuid))

                if msg_type.decode('utf-8') == "SHOUT":
                    group_name = cmds.pop(0)
                    self.log.debug("NODE_MSG GROUP: {}".format(group_name))

                    group_name_2 = cmds.pop(0)
                    self.log.debug("NODE_MSG GROUP_2: {}".format(group_name_2))

                    discoveryMsg = cmds.pop(0)
                    self.log.debug("Discovery Msg : {}".format(discoveryMsg))

                    controller = json.loads(discoveryMsg.decode('utf-8'))
                    self.controller_dl = str(controller["downlink"])
                    self.controller_ul = str(controller["uplink"])
                    self.log.debug("Discovered Controller DL-{}, UL-{}"
                                   .format(self.controller_dl,
                                           self.controller_ul))
                    self.send_event(
                        events.BrokerDiscoveredEvent(
                            self.controller_dl, self.controller_ul)
                    )

        n.stop()
