import time
import pyshark
import trollius as asyncio  # for pyshark comatibility
import threading


__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz}@tkn.tu-berlin.de"


class Sink(object):
    def __init__(self, callback=None):
        self.callback = callback

    def recv(self, packet):
        pass


class RssiSink(Sink):
    def __init__(self, callback=None):
        super().__init__(callback)

    def recv(self, packet):
        if 'radiotap' in packet and 'wlan' in packet:
            rssi = getattr(packet['radiotap'], 'dbm_antsignal', None)
            ta = getattr(packet['wlan'], 'ta_resolved', None)
            if rssi and ta:
                if self.callback:
                    self.callback(str(ta), float(rssi))


class PacketSnifferPyShark():
    """docstring for PacketSnifferPyShark"""

    def __init__(self, iface):
        super().__init__()
        self.snifferThread = None
        self.iface = iface
        self.running = False
        self._mySinks = []

    def start(self):
        self.running = True
        self.snifferThread = threading.Thread(target=self.worker,
                                              name="RssiSnifferPyShark")
        self.snifferThread.setDaemon(True)
        self.snifferThread.start()

    @asyncio.coroutine
    def handler(self):
        capture = pyshark.LiveCapture(interface=self.iface)
        while self.running:
            if not self._mySinks:
                time.sleep(1)

            for packet in capture.sniff_continuously():
                if not self._mySinks:
                    break

                for sink in self._mySinks:
                    sink.recv(packet)

    def worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.handler())
        loop.run_forever()

    def stop(self):
        self.running = False

    def add_sink(self, sink):
        self._mySinks.append(sink)

    def remove_sink(self, sink):
        if sink in self._mySinks:
            self._mySinks.remove(sink)
