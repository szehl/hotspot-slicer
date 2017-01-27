#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time

from uniflex_app_iperf import IperfClientRequestEvent, IperfServerRequestEvent, IperfModule

'''
    Direct iperf app test; without framework.
    Req.: Iperf has to be installed: apt-get install gnuradio
'''
if __name__ == '__main__':

    startServer = True
    startClient = False

    iperf = IperfModule()

    if startServer:
        print('Installing iperf server on node')
        iperfServerEvent = IperfServerRequestEvent()
        #iperfServerEvent.resultReportInterval = 1
        iperfServerEvent.stopAfterFirstReport = True
        iperf.start_iperf_server(iperfServerEvent)
        time.sleep(100)

    #if startClient:
    #    print('Installing iperf client on node')
    #    clientApp0 = uniflex_module_iperf.ClientApplication()
    #    clientApp0.setDestination("192.168.14.142")
    #    clientApp0.setProtocol("TCP")

    #   client_thr = iperf.install_application(clientApp0)
    #    print('Iperf client; throughput is %s' % str(client_thr['throughput']))
