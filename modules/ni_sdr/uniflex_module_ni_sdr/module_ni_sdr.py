import logging
import time
import socket
import datetime
import thread

from sbi.radio_device.net_device import RadioNetDevice
from uniflex.core import modules

__author__ = "Anatolij Zubow, Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{zubow,gawlowicz}@tkn.tu-berlin.de"

"""
Module for IEEE 802.11 SDR platform from National Instruments (NI).

TODO:
- automatic bitfile downloading
"""


class NiSdrModule(modules.DeviceModule, RadioNetDevice):
    def __init__(self):
        super(NiSdrModule, self).__init__()
        self.log = logging.getLogger('NiSdrModule')
        self.MSG_UDP_IP = "127.0.0.1"
        self.MSG_UDP_TX_PORT = 12345
        self.MSG_UDP_RX_PORT = 12346

    def gen_layer2_traffic(self, iface, num_packets, pinter, **kwargs):

        self.log.info('gen80211L2LinkProbing()')
        # get my MAC HW address
        # myMacAddr = self.getHwAddr({'iface': iface})
        # dstMacAddr = 'ff:ff:ff:ff:ff:ff'

        if num_packets > 255:
            num_packets = 255

        MSG_SIZE = 128
        MESSAGE = bytearray(MSG_SIZE)

        self.log.info("UDP target IP: %s " % self.MSG_UDP_IP)
        self.log.info("UDP target port: %d" % self.MSG_UDP_TX_PORT)
        self.log.info("message len: %d" % len(MESSAGE))

        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP

        for pi in range(num_packets):
            sock.sendto(MESSAGE, (self.MSG_UDP_IP, self.MSG_UDP_TX_PORT))
            time.sleep(pinter)

    def sniff_layer2_traffic(self, iface, sniff_timeout):

        self.log.info('sniff_layer2_traffic()')

        BUFFER_SZ = 4096

        rx_pkts = {}
        rx_pkts['res'] = 0

        def ip_monitor_callback():
            sock = socket.socket(socket.AF_INET,  # Internet
                                 socket.SOCK_DGRAM)  # UDP
            sock.bind((self.MSG_UDP_IP, self.MSG_UDP_RX_PORT))

            while True:
                data, addr = sock.recvfrom(BUFFER_SZ)
                rx_pkts['res'] = rx_pkts['res'] + 1

        thread.start_new_thread(ip_monitor_callback, ())

        # wait until timeout
        start = datetime.datetime.now()
        while True:
            now = datetime.datetime.now()
            if (now - start).seconds < sniff_timeout:
                time.sleep(0.1)
            else:
                break

        numRxPkts = rx_pkts['res']
        self.log.info('sniff80211L2LinkProbing(): rxpackets= %d' % numRxPkts)
        return numRxPkts
