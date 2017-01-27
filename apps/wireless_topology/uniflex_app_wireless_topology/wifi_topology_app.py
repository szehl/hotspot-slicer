import logging
import wishful_upis as upis
from uniflex.core import modules
from uniflex.core import events
import itertools
import time
import datetime

__author__ = "Piotr Gawlowicz, Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universitat Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz, zubow}@tkn.tu-berlin.de"


'''
    Wireless topology app for IEEE 802.11:
    - estimates nodes in reception range,
    - estimates nodes in carrier sensing range
'''


class WifiTopologyModule(modules.ControlApplication):
    def __init__(self):
        super().__init__()
        self.log = logging.getLogger('WifiTopologyModule')
        self.nodes = {}

    @modules.on_start()
    def start_wifi_stats_module(self):
        self.log.debug("Start wifi topo module".format())
        self.running = True

    @modules.on_exit()
    def stop_wifi_stats_module(self):
        self.log.debug("Stop wifi topo module".format())
        self.running = False

    @modules.on_event(events.NewNodeEvent)
    def add_node(self, event):
        node = event.node

        self.log.info("Added new node: {}"
                      .format(node.uuid))
        self.nodes[node.uuid] = node

    @modules.on_event(events.NodeExitEvent)
    @modules.on_event(events.NodeLostEvent)
    def remove_node(self, event):
        self.log.info("Node lost".format())
        node = event.node
        reason = event.reason
        if node.uuid in self.nodes:
            del self.nodes[node.uuid]
            self.log.info("Node: {}, removed reason: {}"
                          .format(node.uuid, reason))

    @modules.on_event(upis.wifi.WiFiGetServingAPRequestEvent)
    def get_AP_the_client_is_associated_with(self, event):
        """
        Estimates the AP which serves the given STA.
        Note: if an STA is associated with multiple APs the one with the
        smallest inactivity time is returned.
        """
        sta_mac_addr = event.sta_mac_addr
        wifi_intf = event.wifi_intf

        self.log.info('Function: handle NetFunc event: WiFiGetServingAPRequestEvent')

        try:
            nodes_with_sta = {}

            for node_uuid, node in self.nodes.items():
                res = node.blocking(True).net.get_inactivity_time_of_connected_devices()

                self.log.info(str(res))
                if sta_mac_addr in res:
                    self.log.debug(res[sta_mac_addr])
                    nodes_with_sta[node_uuid] = int(res[sta_mac_addr][0])

                    # dictionary of aps where station is associated
                    self.log.info("STA found on the following APs with the following idle times:")

            if not bool(nodes_with_sta):
                # If no serving AP was found; send None in reply event
                reply_event = upis.wifi.WiFiGetServingAPReplyEvent(sta_mac_addr, wifi_intf, None)
                self.send_event(reply_event)
                return

            # serving AP is the one with minimal STA idle value
            servingAP = min(nodes_with_sta, key=nodes_with_sta.get)
            self.log.info("STA %s is served by AP %s " % (sta_mac_addr, servingAP))

            reply_event = upis.wifi.WiFiGetServingAPReplyEvent(sta_mac_addr, wifi_intf, servingAP)
            self.send_event(reply_event)
            return

        except Exception as e:
            self.log.fatal("An error occurred in get_servingAP: %s" % e)
            raise e


    @modules.on_event(upis.wifi.WiFiGetNodesInCSRangeRequestEvent)
    def estimate_nodes_in_carrier_sensing_range(self, event):
        """
        Test to find out whether two nodes in the network
        are in carrier sensing range using UPIs.
        For a network with N nodes all combinations
        are evaluated, i.e. N over 2.
        Note: make sure ptpd is running: sudo /etc/init.d/ptp-daemon
        @return a list of triples (node1, node2, True/False)
                True/False if nodes are in carrier sensing range
        """

        nodes = list(self.nodes.keys())
        self.log.debug("is_in_carrier_sensing_range for nodes: %s" % str(nodes))

        mon_dev = event.mon_dev
        TAU = event.TAU

        if (len(nodes) < 2):
            self.log.error('For this test we need at least two nodes.')
            return None

        nodeIds = list(range(0, len(nodes)))
        groups = itertools.combinations(nodeIds, 2)
        for subgroup in groups:
            # print(subgroup)
            # testing scenario
            node1_uuid = nodes[subgroup[0]]
            node2_uuid = nodes[subgroup[1]]

            # exec experiment for each pair of nodes
            node1 = self.nodes[node1_uuid]
            node2 = self.nodes[node2_uuid]

            isInCs = self.helper_test_two_node_in_carrier_sensing_range(node1, node2, mon_dev, TAU)


    @modules.on_event(upis.wifi.WiFiTestTwoNodesInCSRangeRequestEvent)
    def test_two_node_in_carrier_sensing_range(self, event):
        """
        Find out whether two nodes are in carrier sensing range or not.
        The following algorithm is used here. The maximum transmit rate of each node is compared to the
        transmission rate which can be achieved by both nodes if they transmit at the same time. If this
        rate is lower than some threshold it is assumed that the nodes can sense each other.
        @return True if nodes are in carrier sensing range
        """

        mon_dev = event.mon_dev
        TAU = event.TAU

        # map from UUID to node
        node1 = self.nodes[event.node1]
        node2 = self.nodes[event.node2]

        self.helper_test_two_node_in_carrier_sensing_range(node1, node2, mon_dev, TAU)


    def helper_test_two_node_in_carrier_sensing_range(self, node1, node2, mon_dev, TAU):
        """
        Helper function to find out whether two nodes are in carrier sensing range or not.
        The following algorithm is used here. The maximum transmit rate of each node is compared to the
        transmission rate which can be achieved by both nodes if they transmit at the same time. If this
        rate is lower than some threshold it is assumed that the nodes can sense each other.
        @return True if nodes are in carrier sensing range
        """

        nodes = []
        nodes.append(node1)
        nodes.append(node2)
        if (len(nodes) < 2):
            self.log.error('For this test we need at least two nodes.')
            return

        self.log.info('Testing carrier sensing range between %s and %s' % (str(node1.uuid), str(node2.uuid)))

        single_tx_rate_stats = {}
        parallel_tx_rate_stats = {}
        rel_rate_cmp_single = {}

        isInCs = {}

        def csResultCollector(group, nodeId, data):
            self.log.info('CS callback %d: receives data msg from %s : %s' % (group, nodeId, data))

            parallel_tx_rate_stats[peer_node] = float(data)
            rel_rate_cmp_single[peer_node] = parallel_tx_rate_stats[peer_node] / single_tx_rate_stats[peer_node]
            self.log.info('Relative rate cmp to single for %s is %.2f' % (peer_node, rel_rate_cmp_single[peer_node]))

            self.log.info('')
            if (len(rel_rate_cmp_single) == 2):
                # done
                if min(rel_rate_cmp_single.values()) <= float(TAU):
                    isInCs['res'] = True
                else:
                    isInCs['res'] = False

        try:
            self.log.debug('(1) single flow at %s' % str(node1))
            rv = node1.blocking(True).net.gen_layer2_traffic(mon_dev, 1000, None, 12, ipPayloadSize=1350, ipdst="1.1.1.1", ipsrc="2.2.2.2", use_tcpreplay=True)

            peer_node = node1
            single_tx_rate_stats[peer_node] = rv

            time.sleep(1)

            self.log.debug('(2) single flow at %s' % str(node2))
            rv = node2.blocking(True).net.gen_layer2_traffic(mon_dev, 1000, None, 12, ipPayloadSize=1350, ipdst="1.1.1.1", ipsrc="2.2.2.2", use_tcpreplay=True)

            peer_node = node2
            single_tx_rate_stats[peer_node] = rv

            self.log.info('single_tx_rate_stats = %s' % str(single_tx_rate_stats))

            time.sleep(1)

            self.log.debug('(3) two flows at same time %s' % str(nodes))
            exec_time = datetime.datetime.now() + datetime.timedelta(seconds=3)
            rv1 = node1.exec_time(exec_time).callback(csResultCollector).net.gen_backlogged_layer2_traffic(mon_dev, 1000, 1350, 12, ipdst="1.1.1.1", ipsrc="2.2.2.2", use_tcpreplay=True)
            rv2 = node2.exec_time(exec_time).callback(csResultCollector).net.gen_backlogged_layer2_traffic(mon_dev, 1000, 1350, 12, ipdst="1.1.1.1", ipsrc="2.2.2.2", use_tcpreplay=True)

            while len(isInCs)==0:
                self.log.debug('waiting for results ...')
                time.sleep(1)

        except Exception as e:
            self.log.fatal("An error occurred (e.g. scheduling events in the past): %s" % e)
            return

        # send reply event
        reply_event = upis.wifi.WiFiTestTwoNodesInCSRangeReplyEvent(node1.uuid, node2.uuid, mon_dev, TAU, isInCs['res'])
        self.send_event(reply_event)

    @modules.on_event(upis.wifi.WiFiGetNodesInCommRangeRequestEvent)
    def estimate_nodes_in_communication_range(self, event):
        """
        Test to find out whether two nodes in the network are in communication range using UPIs.
        For a network with N nodes all combinations are evaluated, i.e. N over 2.
        Note: make sure ptpd is running: sudo /etc/init.d/ptp-daemon
        @return a list of triples (node1, node2, True/False) True/False if nodes are in communication range
        """

        nodes = list(self.nodes.keys())
        self.log.debug("estimate_nodes_in_communication_range for nodes: %s" % str(nodes))

        mon_dev = event.mon_dev
        MINPDR = event.MINPDR

        if (len(nodes) < 2):
            self.log.error('For this test we need at least two nodes.')
            return None

        res = []
        nodeIds = list(range(0, len(nodes)))
        groups = itertools.combinations(nodeIds, 2)
        for subgroup in groups:
            #print(subgroup)
            # testing scenario
            node1_uuid = nodes[subgroup[0]]
            node2_uuid = nodes[subgroup[1]]

            node1 = self.nodes[node1_uuid]
            node2 = self.nodes[node2_uuid]

            # exec experiment for each pair of nodes
            isInComm = self.helper_test_two_nodes_in_communication_range(node1, node2, mon_dev, MINPDR)
            res.append([node1,node2,isInComm])

        return res

    @modules.on_event(upis.wifi.WiFiTestTwoNodesInCommRangeRequestEvent)
    def test_two_node_in_carrier_sensing_range(self, event):
        """
        Find out whether two nodes are in communication range or not.
        """

        mon_dev = event.mon_dev
        MINPDR = event.MINPDR

        # map from UUID to node
        node1 = self.nodes[event.node1]
        node2 = self.nodes[event.node2]

        self.helper_test_two_nodes_in_communication_range(node1, node2, mon_dev, MINPDR)

    def helper_test_two_nodes_in_communication_range(self, node1, node2, mon_dev, MINPDR):
        """
        Helper functions to find out whether two nodes are in communication range using UPIs.
        @return True if nodes are in communication range
        """

        nodes = []
        nodes.append(node1)
        nodes.append(node2)
        if (len(nodes) < 2):
            self.log.error('For this test we need at least two nodes.')
            return None

        self.log.info('Testing communication range between %s and %s' % (str(node1), str(node2)))

        rxPkts = {}

        def csResultCollector(json_message, funcId):
            time_val = json_message['time']
            peer_node = json_message['peer']
            messagedata = json_message['msg']
            self.log.info('CommRange callback %d: receives data msg at %s from %s : %s' % (funcId, str(time_val), peer_node, messagedata))

            if messagedata is None:
                rxPkts['res'] = 0
            else:
                rxPkts['res'] = int(messagedata)

        try:
            self.log.debug('(2) sniff traffic at %s' % str(node1))
            exec_time = datetime.datetime.now() + datetime.timedelta(seconds=2)
            rv = node1.exec_time(exec_time).callback(csResultCollector).net.sniff_layer2_traffic(mon_dev, 5, ipdst="1.1.1.1", ipsrc="2.2.2.2")

            self.log.debug('(2) gen traffic at %s' % str(node2))
            exec_time = datetime.datetime.now() + datetime.timedelta(seconds=3)
            rv = node2.exec_time(exec_time).net.gen_layer2_traffic(mon_dev, 255, 0.01, ipdst="1.1.1.1", ipsrc="2.2.2.2")

            while len(rxPkts)==0:
                self.log.debug('commrange waiting for results ...')
                time.sleep(1)

        except Exception as e:
            self.log.fatal("An error occurred (e.g. scheduling events in the past): %s" % e)
            return

        # calc PDR
        pdr = rxPkts['res'] / float(255)

        minPdrFloat = float(MINPDR)
        self.log.info('PDR between %s and %s is %.2f (%.2f)' % (str(node1), str(node2), pdr, minPdrFloat))

        isInCommRange = False
        if pdr >= minPdrFloat:
            isInCommRange = True

        # send reply event
        reply_event = upis.wifi.WiFiTestTwoNodesInCSRangeReplyEvent(node1.uuid, node2.uuid, mon_dev, MINPDR, isInCommRange)
        self.send_event(reply_event)
