import logging
import inspect
import netifaces as ni
import iptc
from pytc.TrafficControl import TrafficControl
from pyroute2 import IPDB

#from wishful_upis.net import SimpleTable

from uniflex.core import exceptions
from uniflex.core import modules

from sbi.protocols.arp import ArpProtocol
from sbi.protocols.ip import IpProtocol
from sbi.protocols.net_filter import NetFilter
from sbi.protocols.qdisc import Qdisc
from sbi.protocols.tcp import TcpProtocol


__author__ = "Piotr Gawlowicz, Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz, zubow}@tkn.tu-berlin.de"

"""
    Network module for Linux OS.
"""
class NetworkModule(modules.ProtocolModule, ArpProtocol, IpProtocol, NetFilter, Qdisc, TcpProtocol):
    def __init__(self):
        super(NetworkModule, self).__init__()
        self.log = logging.getLogger('NetworkModule')

    def get_ifaces(self):
        """Return the list of interface names
        """
        self.log.info('get_ifaces() called')
        retVal = ni.interfaces()
        return retVal

    def get_iface_hw_addr(self, iface):
        """Return the MAC address of a particular network interface
        """
        try:
            self.log.info('get_iface_hw_addr() called {}'.format(iface))
            retVal = ni.ifaddresses(iface)[ni.AF_LINK][0]['addr']
            return retVal
        except Exception as e:
            self.log.fatal("Failed to get HW address for {}, err_msg: {}"
                           .format(iface, str(e)))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to get HW addr: ' + str(e))

    def get_iface_ip_addr(self, iface):
        """Interfaces may have multiple IP addresses, return a list with all IP addresses
        """
        try:
            self.log.info('get_iface_ip_addr() called {}'.format(iface))
            ipList = [inetaddr['addr'] for inetaddr in ni.ifaddresses(iface)[ni.AF_INET]]
            return ipList
        except Exception as e:
            self.log.fatal("Failed to get IP address for %s, err_msg:%s" % (iface, str(e)))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to get IP addr: ' + str(e))

    def set_ARP_entry(self, iface, mac_addr, ip_addr):
        """
            Adds an entry to the local ARP cache.
            TODO: use Netlink API
        """
        try:
            [rcode, sout, serr] = self.run_command('sudo arp -s ' + ip_addr + ' -i '+ iface + ' ' + mac_addr)
            return sout
        except Exception as e:
            self.log.fatal("Failed to set ARP entry for iface:%s, err_msg:%s" % str(e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to set ARP entry: ' + str(e))

    def change_routing(self, serving_gw_ip_addr, target_gw_ip_addr, dst_ip_addr):
        '''
            Adds entry to routing table.

            IPDB has a simple yet useful routing management interface.
            To add a route, one can use almost any syntax::
            pass spec as is
            r = self.ip.routes.get('192.168.5.0/24')
        '''
        try:
            ip = IPDB(mode='direct')
            r = ip.routes.get(dst_ip_addr + '/32')
            if not r.gateway:
                self.log.info("Currently no gateway found, creating it...")
                ip.routes.add(dst=dst_ip_addr + '/32', gateway=target_gw_ip_addr).commit()
            else:
                self.log.info("Old gateway = %s for %s" % (r.gateway, dst_ip_addr))

                if (r.gateway.startswith(serving_gw_ip_addr) or r.gateway.startswith(target_gw_ip_addr)):
                    r.remove()

                ip.routes.add(dst=dst_ip_addr + '/32', gateway=target_gw_ip_addr).commit()

                r = ip.routes.get(dst_ip_addr + '/32')
                self.log.info("New gateway = %s for %s" % (r.gateway, dst_ip_addr))

            ip.release()
            return True

        except Exception as e:
            self.log.fatal("Failed to change routing, err_msg:%s" % str(e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to change routing: ' + str(e))

    def set_netem_profile(self, iface, profile):
        """
            Sets the network emulation parameters
        """
        self.log.debug('set_profile on interface: {}'.format(iface))

        tcMgr = TrafficControl()
        intface = tcMgr.getInterface(iface)
        intface.setProfile(profile)
        return True

    def update_netem_profile(self, iface, profile):
        """
            Updates the network emulation parameters
        """
        self.log.debug('updateProfile on interface: {}'.format(iface))

        tcMgr = TrafficControl()
        intface = tcMgr.getInterface(iface)
        intface.updateProfile(profile)
        return True

    def remove_netem_profile(self, iface):
        """
            Removes the network emulation parameters
        """
        self.log.debug('removeProfile on interface: {}'.format(iface))

        tcMgr = TrafficControl()
        intface = tcMgr.getInterface(iface)
        intface.clean()
        return True

    def set_per_link_netem_profile(self, iface, dstIpAddr, profile):
        """
            Sets per link network emulation parameters
        """
        self.log.debug('setPerLinkProfile on interface: {}'.format(iface))

        tcMgr = TrafficControl()
        intface = tcMgr.getInterface(iface)
        intface.setPerLinkProfile(profile, dstIpAddr)
        return True

    def remove_per_link_netem_profile(self, iface, dstIpAddr):
        """
            Remove per link network emulation parameters
        """
        self.log.debug('removePerLinkProfile on interface: {}'.format(iface))

        tcMgr = TrafficControl()
        intface = tcMgr.getInterface(iface)
        intface.cleanPerLinkProfile(dstIpAddr)
        return True

    def update_per_link_netem_profile(self, iface, dstIpAddr, profile):
        """
            Update per link network emulation parameters
        """
        self.log.debug('updatePerLinkProfile on interface: {}'.format(iface))

        tcMgr = TrafficControl()
        intface = tcMgr.getInterface(iface)
        intface.updatePerLinkProfile(profile, dstIpAddr)
        return True

    def install_egress_scheduler(self, iface, scheduler):
        """
            Traffic control: install egress scheduler
        """
        self.log.debug('installEgressScheduler on interface: {}'.format(iface))

        tcMgr = TrafficControl()
        intface = tcMgr.getInterface(iface)
        intface.setEgressScheduler(scheduler)
        return True

    def remove_egress_scheduler(self, iface):
        """
            Traffic control: remove egress scheduler
        """
        self.log.debug('removeEgressScheduler on interface: {}'.format(iface))

        tcMgr = TrafficControl()
        intface = tcMgr.getInterface(iface)
        intface.clean()
        tcMgr.cleanIpTables()
        return True

    def clear_nf_tables(self, table="ALL", chain="ALL"):
        """
            Clear IP tables
        """
        self.log.debug('clearIpTables'.format())

        tables = []
        chains = {}

        if table == "ALL":
            tables = ["raw", "mangle", "nat", "filter"]
        else:
            if not isinstance(table, list):
                table = [table]
            tables.extend(table)

        if chain == "ALL":
            chains["filter"] = ["INPUT", "FORWARD", "OUTPUT"]
            chains["nat"] = ["PREROUTING", "OUTPUT", "POSTROUTING"]
            chains["mangle"] = ["PREROUTING", "OUTPUT", "INPUT", "FORWARD", "POSTROUTING"]
            chains["raw"] = ["PREROUTING", "OUTPUT"]
        else:
            if not isinstance(chain, list):
                chain = [chain]
            chains[tables[0]].extend(chain)

        for tableName in tables:
            for chainName in chains[tableName]:
                chain = iptc.Chain(iptc.Table(tableName), chainName)
                chain.flush()

        return True

    def get_nf_table(self, tableName):
        """
            Get IP tables
        """
        self.log.debug('getIpTable'.format())

        # exec embedded function
        table = iptc.Table(tableName)
        # refresh table to get current counters
        table.refresh()
        # create simple table (ie. without pointers to ctypes)
        # simpleTable = SimpleTable(table)
        # return simpleTable
        return None

    def set_pkt_marking(self, flowId, markId=None,
                        table="mangle", chain="POSTROUTING"):
        """
            Mark packets
        """
        self.log.debug('setMarking'.format())

        if not markId:
            tcMgr = TrafficControl()
            markId = tcMgr.generateMark()

        rule = iptc.Rule()

        if flowId.srcAddress:
            rule.src = flowId.srcAddress

        if flowId.dstAddress:
            rule.dst = flowId.dstAddress

        if flowId.prot:
            rule.protocol = flowId.prot
            match = iptc.Match(rule, flowId.prot)

            if flowId.srcPort:
                match.sport = flowId.srcPort

            if flowId.dstPort:
                match.dport = flowId.dstPort

            rule.add_match(match)

        target = iptc.Target(rule, "MARK")
        target.set_mark = str(markId)
        rule.target = target
        chain = iptc.Chain(iptc.Table(table), chain)
        chain.insert_rule(rule)
        return markId

    def del_pkt_marking(self, flowId, markId,
                        table="mangle", chain="POSTROUTING"):
        """
            Unmark packets
        """
        # TODO: store table and chain per flowId/mark in set_pkt_marking,
        # it should be possible to remove marking only with flowId/markId
        self.log.debug('delMarking'.format())

        rule = iptc.Rule()

        if flowId.srcAddress:
            rule.src = flowId.srcAddress

        if flowId.dstAddress:
            rule.dst = flowId.dstAddress

        if flowId.prot:
            rule.protocol = flowId.prot
            match = iptc.Match(rule, flowId.prot)

            if flowId.srcPort:
                match.sport = flowId.srcPort

            if flowId.dstPort:
                match.dport = flowId.dstPort

            rule.add_match(match)

        target = iptc.Target(rule, "MARK")
        target.set_mark = str(markId)
        rule.target = target
        chain = iptc.Chain(iptc.Table(table), chain)
        chain.delete_rule(rule)
        return True

    def set_ip_tos(self, flowId, tos, table="mangle", chain="POSTROUTING"):
        """
            Set IP ToS field
        """
        self.log.debug('setTos'.format())

        rule = iptc.Rule()

        if flowId.srcAddress:
            rule.src = flowId.srcAddress

        if flowId.dstAddress:
            rule.dst = flowId.dstAddress

        if flowId.prot:
            rule.protocol = flowId.prot
            match = iptc.Match(rule, flowId.prot)

            if flowId.srcPort:
                match.sport = flowId.srcPort

            if flowId.dstPort:
                match.dport = flowId.dstPort

            rule.add_match(match)

        target = iptc.Target(rule, "TOS")
        target.set_tos = str(tos)
        rule.target = target
        chain = iptc.Chain(iptc.Table(table), chain)
        chain.insert_rule(rule)
        return True

    def del_ip_tos(self, flowId, tos, table="mangle", chain="POSTROUTING"):
        """
            Disable IP ToS mangling
        """
        # TODO: store table and chain per flowId/mark in set_pkt_marking,
        # it should be possible to remove marking only with flowId/markId
        self.log.debug('delTos'.format())

        rule = iptc.Rule()

        if flowId.srcAddress:
            rule.src = flowId.srcAddress

        if flowId.dstAddress:
            rule.dst = flowId.dstAddress

        if flowId.prot:
            rule.protocol = flowId.prot
            match = iptc.Match(rule, flowId.prot)

            if flowId.srcPort:
                match.sport = flowId.srcPort

            if flowId.dstPort:
                match.dport = flowId.dstPort

            rule.add_match(match)

        target = iptc.Target(rule, "TOS")
        target.set_tos = str(tos)
        rule.target = target
        chain = iptc.Chain(iptc.Table(table), chain)
        chain.delete_rule(rule)
        return True
