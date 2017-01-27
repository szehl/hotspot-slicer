import os
import signal
import logging
import subprocess
import inspect
import binascii
from datetime import datetime
# pip install -U -e git+https://github.com/wraith-wireless/PyRIC#egg=pyric
import pyric                           # pyric error (and ecode EUNDEF)
from pyric import pyw                  # for iw functionality
import pyric.utils.hardware as hw      # for chipset/driver
from pyric.utils.channels import rf2ch  # rf to channel conversion
from pyric.utils.channels import ch2rf  # rf to channel conversion
from pyroute2 import IW

from .packet_sniffer import PacketSnifferPyShark, RssiSink
from scapy.all import *

# this is just for Pycharm; do not remove
from scapy.layers.dot11 import Dot11
from scapy.layers.dot11 import RadioTap
from scapy.layers.inet import IP
from scapy.layers.l2 import LLC, SNAP

from sbi.wifi.net_device import WiFiNetDevice
from sbi.wifi.events import RssiSampleEvent
from uniflex.core import modules
from uniflex.core import exceptions

__author__ = "Piotr Gawlowicz, Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz, zubow}@tkn.tu-berlin.de"


class WifiModule(modules.DeviceModule, WiFiNetDevice):
    def __init__(self):
        super(WifiModule, self).__init__()
        self.log = logging.getLogger('WifiModule')
        self.phyName = None
        self.phyIndex = None
        self.channel = None
        self.power = None
        self.packetSniffer = None

    @modules.on_start()
    def my_start_function(self):
        found = False
        for card in pyw.phylist():
            if card[1] == self.device:
                found = True
                self.phyIndex = card[0]
                self.phyName = card[1]

        if not found:
            self.log.info("Device {} not found".format(self.device))
            raise exceptions.UniFlexException(msg='Device not found')

        else:
            self.log.info("Device {} found, index: {}"
                          .format(self.phyName, self.phyIndex))

        cmd = "rfkill unblock wifi"
        self.run_command(cmd)

    ''' Helper '''

    def _get_my_ifaces(self):
        myWInterfaces = []
        for ifName in pyw.winterfaces():
            card = pyw.getcard(ifName)
            if card.phy == self.phyIndex:
                myWInterfaces.append(ifName)
        return myWInterfaces

    def _check_if_my_iface(self, ifaceName):
        if not pyw.iswireless(ifaceName):
            return False

        myIfaces = self._get_my_ifaces()
        if ifaceName in myIfaces:
            return True

        return False

    ''' API '''

    def get_interfaces(self):
        ifaces = self._get_my_ifaces()
        return ifaces


    def get_interface_info(self, ifaceName):
        if not self._check_if_my_iface(ifaceName):
            self.log.error('check_if_my_iface failed')
            raise exceptions.FunctionExecutionFailed(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='No such interface: ' + ifaceName)

        dinfo = pyw.devinfo(ifaceName)
        # Delete card object from dict
        dinfo.pop("card", None)
        return dinfo


    def get_phy_info(self, ifaceName):
        if not self._check_if_my_iface(ifaceName):
            self.log.error('check_if_my_iface failed')
            raise exceptions.FunctionExecutionFailed(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='No such interface: ' + ifaceName)

        dinfo = pyw.devinfo(ifaceName)
        card = dinfo['card']
        pinfo = pyw.phyinfo(card)
        return pinfo


    def add_interface(self, ifaceName, mode, **kwargs):
        if ifaceName in pyw.winterfaces():
            return False

        iw = IW()
        mode2int = {'adhoc': 1,
                    'sta': 2,
                    'station': 2,
                    'managed': 2,
                    'ap': 3,
                    'ap_vlan': 4,
                    'wds': 5,
                    'monitor': 6,
                    'mesh_point': 7,
                    'p2p_client': 8,
                    'p2p_go': 9,
                    'p2p_device': 10,
                    'ocb': 11}

        modeInt = mode2int.get(mode, None)
        if modeInt is None:
            return False

        iw.add_interface(ifaceName, modeInt, None, 0)

        ''' Other option:
        w0 = pyw.getcard('wlan1‘)
        if 'monitor' in pyw.devmodes(w0):
            m0 = pyw.devadd(w0,'mon0','monitor’)

           pyw.winterfaces()
           pyw.up(m0) # bring the new card up to use
           pyw.chset(m0,6,None)
        '''

        return True


    def del_interface(self, ifaceName):
        card = self.get_wifi_chard(ifaceName)  # get a card for interface
        pyw.devdel(card)


    def set_interface_up(self, ifaceName):
        card = self.get_wifi_chard(ifaceName)  # get a card for interface
        # TODO: replace by pyric rfkill
        cmd = "rfkill unblock wifi"
        self.run_command(cmd)
        pyw.up(card)
        return pyw.isup(card)


    def set_interface_down(self, ifaceName):
        card = self.get_wifi_chard(ifaceName)  # get a card for interface
        pyw.down(card)
        return True


    def is_interface_up(self, ifaceName):
        w0 = self.get_wifi_chard(ifaceName)  # get a card for interface
        return pyw.isup(w0)


    def is_connected(self, ifaceName):
        card = self.get_wifi_chard(ifaceName)  # get a card for interface
        return pyw.isconnected(card)


    def connect_to_network(self, iface, ssid):
        self.log.info('Connecting via to AP with SSID: %s->%s' %
                      (str(iface), str(ssid)))

        cmd_str = 'sudo iwconfig ' + iface + ' essid ' + str(ssid)

        try:
            [rcode, sout, serr] = self.run_command(cmd_str)
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=fname, err_msg=str(e))

        return True


    def disconnect(self, ifaceName):
        card = self.get_wifi_chard(ifaceName)  # get a card for interface
        pyw.disconnect(card)


    def get_link_info(self, ifaceName):
        '''
        For each link we get:
            stat associated
            ssid ****net
            bssid XX:YY:ZZ:00:11:22
            chw 20
            int 100
            freq 5765
            tx {'pkts': 256, 'failed': 0, 'bytes': 22969,
                'bitrate': {'rate': 6.0}, 'retries': 31}
            rx {'pkts': 29634, 'bitrate': {'width': 40, 'rate': 270.0,
                'mcs-index': 14, 'gi': 0}, 'bytes': 2365454}
            rss -50
        '''

        card = self.get_wifi_chard(ifaceName)  # get a card for interface
        link = pyw.link(card)
        return link


    def scan_networks(self, ifaceName):
        try:
            # TODO: replace with pyric
            cmd = 'iw dev ' + ifaceName + ' scan'
            [rcode, sout, serr] = self.run_command(cmd)
            return sout
        except Exception as e:
            self.log.fatal("An error occurred in Dot80211Linux: %s" % e)
            raise Exception("An error occurred in Dot80211Linux: %s" % e)

    ''' TX power control '''

    def set_tx_power(self, power_dBm, ifaceName):
        """
        Sets TX power for that interface
        :param power_dBm: the power in dBm
        :param ifaceName: name of interface
        :return: True in case it was successful
        """

        self.log.info('Setting power on iface {}:{} to {}'
                      .format(ifaceName, self.device, str(power_dBm)))
        try:
            w0 = self.get_wifi_chard(ifaceName)  # get a card for interface
            pyw.txset(w0, 'fixed', power_dBm)
            self.power = power_dBm
        except Exception as e:
            raise exceptions.FunctionExecutionFailed(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to set tx power: ' + str(e))

        return True


    def get_tx_power(self, ifaceName):
        """
        Gets the TX power used by this interface
        :param ifaceName: name of the interface
        :return: power in dBm
        """

        self.log.debug("getting power of interface: {}".format(ifaceName))
        w0 = self.get_wifi_chard(ifaceName)  # get a card for interface
        self.power = pyw.txget(w0)
        return self.power

    ''' Rf channel assignment '''

    def set_channel(self, channel, ifaceName, **kwargs):
        """
        Set the Rf channel
        :param channel: the new channel, i.e. channel number according to IEEE 802.11 spec
        :param ifaceName: name of the interface
        :param kwargs: optional args, i.e. path to control socket
        :return: True in case it was successful
        """

        self.log.info('Setting channel for {}:{} to {}'
                      .format(ifaceName, self.device, channel))
        try:
            w0 = self.get_wifi_chard(ifaceName)  # get a card for interface
            # check mode
            dinfo = pyw.devinfo(w0)
            if dinfo['mode'] == 'AP':
                if not "control_socket_path" in kwargs:
                    self.log.warn('Please pass the path to hostapd control socket')
                    return False

                # pass new chanel to hostapd
                # hostapd requires frequency not channel
                freq = ch2rf(channel)
                control_socket_path = kwargs["control_socket_path"]
                beacon_periods = 5
                cmd = ('sudo hostapd_cli -p {} chan_switch {} {}'
                       .format(control_socket_path, beacon_periods, freq))
                self.run_command(cmd)
            else:
                # chw: channel width oneof {None|'HT20'|'HT40-'|'HT40+'}
                chw = None
                pyw.chset(w0, channel, chw)
                self.channel = channel
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.FunctionExecutionFailed(
                func_name=fname, err_msg=str(e))
        return True


    def get_channel(self, ifaceName, **kwargs):
        """
        Get the current used Rf channel number according to IEEE 802.11 spec
        :param ifaceName: name of interface
        :param kwargs: optional arg
        :return: the channel number
        """

        self.log.info('Get channel for {}:{}'
                      .format(ifaceName, self.device))
        w0 = self.get_wifi_chard(ifaceName)  # get a card for interface
        self.channel = pyw.chget(w0)
        return self.channel


    def get_info_of_connected_devices(self, ifaceName):
        '''
            Returns information about associated STAs
            for a node running in AP mode
            tbd: use Netlink API
        '''

        self.log.info("WIFI Module get info on assoc clients on iface: %s" % str(ifaceName))

        try:
            [rcode, sout, serr] = self.run_command(
                'iw dev ' + ifaceName + ' station dump')

            # mac_addr -> stat_key -> list of (value, unit)
            res = {}
            sout_arr = sout.split("\n")

            for line in sout_arr:
                s = line.strip()
                if s == '':
                    continue
                if "Station" in s:
                    arr = s.split()
                    mac_addr = arr[1].strip()
                    res[mac_addr] = {}
                else:
                    arr = s.split(":")
                    key = arr[0].strip()
                    val = arr[1].strip()

                    arr2 = val.split()
                    val2 = arr2[0].strip()

                    if len(arr2) > 1:
                        unit = arr2[1].strip()
                    else:
                        unit = None

                    res[mac_addr][key] = (val2, unit)
            return res
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=fname, err_msg=str(e))


    def get_inactivity_time_of_connected_devices(self, iface):
        return self.get_entry_of_connected_devices('inactive time', iface)


    def get_avg_sigpower_of_connected_devices(self, iface):
        return self.get_entry_of_connected_devices('signal avg', iface)


    def get_sigpower_of_connected_devices(self, iface):
        return self.get_entry_of_connected_devices('signal', iface)


    def get_tx_retries_of_connected_devices(self, iface):
        return self.get_entry_of_connected_devices('tx retries', iface)


    def get_tx_packets_of_connected_devices(self, iface):
        return self.get_entry_of_connected_devices('tx packets', iface)


    def get_tx_failed_of_connected_devices(self, iface):
        return self.get_entry_of_connected_devices('tx failed', iface)


    def get_tx_bytes_of_connected_devices(self, iface):
        return self.get_entry_of_connected_devices('tx bytes', iface)


    def get_tx_bitrate_of_connected_devices(self, iface):
        return self.get_entry_of_connected_devices('tx bitrate', iface)


    def get_rx_bytes_of_connected_devices(self, iface):
        return self.get_entry_of_connected_devices('rx bytes', iface)


    def get_rx_packets_of_connected_devices(self, iface):
        return self.get_entry_of_connected_devices('rx packets', iface)


    def get_authorized_connected_device(self, iface):
        return self.get_entry_of_connected_devices('authorized', iface)


    def get_authenticated_connected_device(self, iface):
        return self.get_entry_of_connected_devices('authenticated', iface)


    def get_used_preamble_connected_device(self, iface):
        return self.get_entry_of_connected_devices('preamble', iface)


    def get_mfp_connected_device(self, iface):
        return self.get_entry_of_connected_devices('MFP', iface)


    def get_wmm_wme_connected_device(self, iface):
        return self.get_entry_of_connected_devices('WMM/WME', iface)


    def get_tdls_peer_connected_device(self, iface):
        return self.get_entry_of_connected_devices('TDLS peer', iface)


    def getHwAddr(self, ifaceName):
        w0 = self.get_wifi_chard(ifaceName)  # get a card for interface
        mac = pyw.macget(w0)
        return mac


    def getIfaceIpAddr(self, ifaceName):
        w0 = self.get_wifi_chard(ifaceName)  # get a card for interface
        ip = pyw.inetget(w0)[0]
        return ip


    def gen_layer2_traffic(self, iface, num_packets,
                           pkt_interval, max_phy_broadcast_rate_mbps,
                           **kwargs):

        self.log.info('gen_layer2_traffic ... here 802.11()')

        ipdst = kwargs.get('ipdst')
        ipsrc = kwargs.get('ipsrc')

        # get my MAC HW address
        myMacAddr = self.getHwAddr(iface)
        dstMacAddr = 'ff:ff:ff:ff:ff:ff'

        if pkt_interval is not None:
            # generate with some packet interval
            if num_packets > 255:
                num_packets = 255

            data = (RadioTap() /
                    Dot11(type=2, subtype=0, addr1=dstMacAddr,
                          addr2=myMacAddr, addr3=myMacAddr) /
                    LLC() /
                    SNAP() /
                    IP(dst=ipdst, src=ipsrc, ttl=(1, num_packets)))
            sendp(data, iface=iface, inter=pkt_interval)

            return 1.0 / pkt_interval
        else:
            assert max_phy_broadcast_rate_mbps is not None
            ipPayloadSize = kwargs["ipPayloadSize"]
            phyBroadcastMbps = kwargs["phyBroadcastMbps"]

            use_tcpreplay = kwargs.get('use_tcpreplay')

            # craft packet to be transmitted
            payload = 'Z' * ipPayloadSize
            data = (RadioTap() /
                    Dot11(type=2, subtype=0, addr1=dstMacAddr,
                          addr2=myMacAddr, addr3=myMacAddr) /
                    LLC() /
                    SNAP() /
                    IP(dst=ipdst, src=ipsrc) /
                    payload)

            # send 10 packets backlogged
            now = datetime.now()
            if use_tcpreplay:
                # use tcprelay
                sendpfast(data, iface=iface, mbps=phyBroadcastMbps,
                          loop=num_packets, file_cache=True)
            else:
                piter = (len(data) * 8) / (phyBroadcastMbps * 1e6)
                sendp(data, iface=iface, loop=1, inter=piter,
                      realtime=True, count=num_packets, verbose=0)

            delta = datetime.now() - now
            myDelta = delta.seconds + delta.microseconds / 1000000.0
            # calc achieved transmit data rate
            tx_frame_rate = (1.0 /
                             (myDelta / num_packets))

            self.log.info('gen80211L2LinkProbing(): tx_frame_rate=%d' %
                          int(tx_frame_rate))

            return tx_frame_rate


    def sniff_layer2_traffic(self, iface, sniff_timeout, **kwargs):

        self.log.info('sniff layer 2 traffic ... here 802.11')

        # some additional filtering ...todo!!!!!!!
        ipdst = kwargs.get('ipdst')
        ipsrc = kwargs.get('ipsrc')

        rx_pkts = {}
        rx_pkts['res'] = 0

        def ip_monitor_callback(pkt):
            if IP in pkt and pkt[IP].src == ipsrc and pkt[IP].dst == ipdst:
                rx_pkts['res'] = rx_pkts['res'] + 1
                # return pkt.sprintf("{IP:%IP.src% -> %IP.dst% -> %IP.ttl%\n}")

        sniff(iface=iface, prn=ip_monitor_callback, timeout=sniff_timeout)

        numRxPkts = rx_pkts['res']
        self.log.info('sniff80211L2LinkProbing(): rxpackets= %d' % numRxPkts)
        return numRxPkts


    def inject_frame(self, iface, frame, is_layer_2_packet,
                     tx_count=1, pkt_interval=1):
        self.log.debug("Inject frame".format())

        if is_layer_2_packet:
            sendp(frame, iface=iface, inter=pkt_interval,
                  realtime=True, count=tx_count, verbose=0)
        else:
            send(frame, iface=iface, inter=pkt_interval,
                 realtime=True, count=tx_count, verbose=0)

        return True


    def disconnect_device(self, iface, sta_mac_addr):
        """
        Send a disaccociation request frame
        to a client STA associated with this AP.
        tbd: what is -p ?? Please simplify
        """

        exec_file = 'sudo hostapd_cli'
        args = '-p /tmp/hostapd-' + iface + ' disassociate'

        command = exec_file + ' ' + args + ' ' + sta_mac_addr
        self.log.debug('Disassociate STA %s on iface %s' %
                       (sta_mac_addr, iface))
        self.log.debug('exe: %s' % command)

        try:
            [rcode, sout, serr] = self.run_command(command)
            return sout
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=fname, err_msg=str(e))


    def remove_device_from_blacklist(self, iface, sta_mac_addr):
        """
        Unblacklist a given STA in the AP,
        i.e. the STA is able to associate with this AP afterwards.
        tbd: what is -p ?? Please simplify
        """

        exec_file = 'sudo hostapd_cli'
        args = '-p /tmp/hostapd-' + iface + ' unblacklist_sta'

        command = exec_file + ' ' + args + ' ' + sta_mac_addr
        self.log.debug('exe: %s' % command)
        self.log.debug('Unblacklist node %s on iface %s' %
                       (sta_mac_addr, iface))

        try:
            [rcode, sout, serr] = self.run_command(command)
            return sout
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=fname, err_msg=str(e))


    def add_device_to_blacklist(self, iface, sta_mac_addr):
        """
        Blacklist a given STA in the AP, i.e. any request
        for association by the STA will be ignored by the AP.
        tbd: what is -p ?? Please simplify
        """

        exec_file = 'sudo hostapd_cli'
        args = '-p /tmp/hostapd-' + iface + ' blacklist_sta'

        command = exec_file + ' ' + args + ' ' + sta_mac_addr
        self.log.debug('Blacklist node %s on iface %s' % (sta_mac_addr, iface))
        self.log.debug('exec %s' % command)

        try:
            [rcode, sout, serr] = self.run_command(command)
            return sout
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=fname, err_msg=str(e))


    def register_new_device(self, iface, sta_mac_addr):
        """
        Register a new STA within the AP,
        i.e. afterwards the STA is able to exchange data frames.
        tbd: consider client capabilities
        """

        self.log.debug('Add new STA %s on iface %s' % (sta_mac_addr, iface))

        exec_file = 'sudo hostapd_cli'

        self.log.debug('exec path: %s' % exec_file)

        try:
            cmd = "{} -p /tmp/hostapd-{}  new_sta {}".format(exec_file,
                                                             iface,
                                                             sta_mac_addr)
            [rcode, sout, serr] = self.run_command(cmd)
            return sout
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=fname, err_msg=str(e))


    def trigger_channel_switch_in_device(self, iface, sta_mac_addr,
                                         target_channel, serving_channel,
                                         **kwargs):
        """
        Transmit Channel Switch Announcement
        (CSA) beacon to the given STA.
        """

        bssid = kwargs.get('bssid')
        self.log.debug('Sending CSA to {} on iface {}'
                       .format(sta_mac_addr, iface),
                       ' with BSSID {} switch STA to channel {}'
                       .format(bssid, str(target_channel)))

        # tbd: clean up this mess
        data1 = ('3bc0904f0000000064000100000542494741500',
                 '1088c129824b048606c0301')
        data2 = ('050400020000070c44452024081464051a84031a2d1a0c001bffff',
                 '0000000000000000000001000000000000000000003d162c000400',
                 '0000000000000000000000000000000000007f0800000000000000',
                 '40dd180050f2020101800003a4000027a4000042435d0062322e00',
                 'dd06aaaaaa3f4325dd14aaaaaa8020544b4e2d4c6f57532d537973',
                 '74656ddd06aaaaaa215a01250300')
        beacon = (RadioTap() /
                  Dot11(type=0, subtype=8, addr1=sta_mac_addr,
                        addr2=bssid, addr3=bssid) /
                  binascii.unhexlify(
                  data1 + hex(serving_channel).replace("0x", "") + data2 +
                  hex(target_channel).replace("0x", "") + '00'))

        # tbd: do we really need this
        BEACON_ARQ = 3
        for ii in range(BEACON_ARQ):
            # repetitive transmission
            sendp(beacon, iface=iface)
        return True


    def send_rssi_event(self, ta, rssi):
        self.log.debug("RSSI sample: TA: {}, value: {}"
                       .format(ta, rssi))
        sampleEvent = RssiSampleEvent(ta=ta, rssi=rssi)
        self.send_event(sampleEvent)


    def rssi_service_start(self):
        self._rssiServiceRunning = True
        # iface = event.iface
        iface = 'mon0'

        if not self.packetSniffer:
            self.packetSniffer = PacketSnifferPyShark(iface=iface)
            self.packetSniffer.start()

        self.rssiSink = RssiSink(callback=self.send_rssi_event)
        self.packetSniffer.add_sink(self.rssiSink)


    def rssi_service_stop(self):
        self._rssiServiceRunning = False


    def get_regulatory_domain(self):
        '''
        Returns the regulatory domain
        '''
        return pyw.regget()


    def set_regulatory_domain(self, new_domain):
        '''
        Sets the regulatory domain
        '''
        return pyw.regset(new_domain)


    def is_rf_blocked(self, iface):
        '''
        Returns information about rf blocks (Soft Block, Hard Block)
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        return pyw.isblocked(w0)


    def rf_unblock(self, iface):
        '''
        Turn off the softblock
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        pyw.unblock(w0)  # turn off the softblock


    def set_mac_address(self, iface, new_mac_addr):
        '''
        Sets a new MAC address on wireless interface
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        pyw.macset(w0, new_mac_addr)


    def set_power_management(self, iface, value):
        '''
        Sets power management
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        pyw.pwrsaveset(w0, value)


    def get_power_management(self, iface):
        '''
        Get power management
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        return pyw.pwrsaveget(w0)


    def set_retry_short(self, iface, value):
        '''
        Sets retry short
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        pyw.retryshortset(w0, value)


    def get_retry_short(self, iface):
        '''
        Get retry short
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        return pyw.retryshortget(w0)


    def set_retry_long(self, iface, value):
        '''
        Sets retry long
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        pyw.retrylongset(w0, value)


    def get_retry_long(self, iface):
        '''
        Get retry long
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        return pyw.retrylongget(w0)


    def set_rts_threshold(self, iface, value):
        '''
        Sets RTS threshold
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        pyw.rtsthreshset(w0, value)


    def get_rts_threshold(self, iface):
        '''
        Get RTS threshold
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        return pyw.rtsthreshget(w0)


    def set_fragmentation_threshold(self, iface, value):
        '''
        Sets framgmentation threshold
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        pyw.fragthreshset(w0, value)


    def get_fragmentation_threshold(self, iface):
        '''
        Get framgmentation threshold
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        return pyw.fragthreshget(w0)


    def get_supported_modes(self, iface):
        '''
        Get supported WiFi modes
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        pinfo = pyw.phyinfo(w0)
        return pinfo['modes']


    def get_supported_swmodes(self, iface):
        '''
        Get supported WiFi software modes
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        pinfo = pyw.phyinfo(w0)
        return pinfo['swmodes']


    def get_rf_band_info(self, iface):
        '''
        Get info about supported RF bands
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        pinfo = pyw.phyinfo(w0)
        return pinfo['bands']


    def get_ciphers(self, iface):
        '''
        Get info about supported ciphers
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        pinfo = pyw.phyinfo(w0)
        return pinfo['ciphers']


    def get_supported_wifi_standards(self, iface):
        '''
        Get info about supported WiFi standards, i.e. 802.11a/n/g/ac/b
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        return pyw.devstds(w0)


    def set_modulation_rate(self, ifaceName, is5Ghzband,
                            isLegacy, rate_Mbps_or_ht_mcs):
        '''
        Sets a fix PHY modulation rate:
        - legacy: bitrate
        - 11n/ac: ht_mcs
        '''

        try:
            if isLegacy:
                arg = 'legacy'
            else:
                arg = 'ht-mcs'

            if is5Ghzband:
                arg = arg + '-5'
            else:
                arg = arg + '-2.4'

                arg = arg + ' ' + rate_Mbps_or_ht_mcs

            [rcode, sout, serr] = self.run_command(
                'iw dev ' + ifaceName + ' set bitrates ' + arg)

        except Exception as e:
            self.log.fatal("Failed to set bitrate: %s" % str(e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg=str(e))


    def get_wifi_mode(self, iface):
        '''
        Get the mode of the interface: managed, monitor, ...
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        return pyw.modeget(w0)


    def get_info(self, iface=None):
        '''
        Get info about the wifi card: vendor, driver, ...
        '''
        w0 = self.get_wifi_chard(iface)  # get a card for interface
        return pyw.ifinfo(w0)

    #################################################
    # Helper functions
    #################################################

    def get_wifi_chard(self, iface):
        '''
        Get WiFi chard
        '''

        if not self._check_if_my_iface(iface):
            self.log.error('check_if_my_iface failed')
            raise exceptions.FunctionExecutionFailed(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='No such interface: ' + iface)

        return pyw.getcard(iface)  # get a card for interface


    def get_entry_of_connected_devices(self, key, iface):

        try:
            res = self.get_info_of_connected_devices(iface)

            rv = {}
            for mac_addr in res:
                value = res[mac_addr][key]
                self.log.info('%s -> %s' % (mac_addr, value))
                rv[mac_addr] = value

            # dict of mac_addr -> value
            return rv
        except Exception as e:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("An error occurred in %s: %s" % (fname, e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=fname, err_msg=str(e))


    def run_command(self, command):
        '''
        Method to start the shell commands
        and get the output as iterater object
        '''

        sp = subprocess.Popen(command, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, shell=True)
        out, err = sp.communicate()

        if False:
            if out:
                self.log.debug("standard output of subprocess:")
                self.log.debug(out)
            if err:
                self.log.debug("standard error of subprocess:")
                self.log.debug(err)

        if err:
            raise Exception("An error occurred in Dot80211Linux: %s" % err)

        return [sp.returncode, out.decode("utf-8"), err.decode("utf-8")]


    def run_timeout_command(self, command, timeout):
        """
            Call shell-command and either return its output or kill it
            if it doesn't normally exit within timeout seconds and return None
        """
        cmd = command.split(" ")
        start = datetime.now()
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(0.1)
            now = datetime.now()
            if (now - start).seconds > timeout:
                os.kill(process.pid, signal.SIGKILL)
                os.waitpid(-1, os.WNOHANG)
                return process.stdout.read()
        return process.stdout.read()
