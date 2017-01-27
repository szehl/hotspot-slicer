import sys
import inspect
import logging
import subprocess

import time
from uniflex.core import exceptions
from uniflex.core import modules
from uniflex.core import events
from uniflex.core.common import UniFlexThread

from .events import IperfServerRequestEvent, IperfClientRequestEvent, IperfSampleEvent

__author__ = "Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universitat Berlin"
__version__ = "0.1.0"
__email__ = "{zubow}@tkn.tu-berlin.de"


class ResultScanner(UniFlexThread):
    """
        Thread scanning for throughput results.
    """

    def __init__(self, module, isServer, stopAfterFirstReport, process):
        super().__init__(module)
        self.log = logging.getLogger('iperf_module.scanner')
        self.log.debug('starting scanner for iperf')
        self.isServer = isServer
        self.stopAfterFirstReport = stopAfterFirstReport
        self.process = process


    def task(self):
        self.log.debug('started scanner for iperf')
        while not self.is_stopped():
            #time.sleep(0.1)
            line = self.process.stdout.readline()
            line = line.decode('utf-8')
            throughput = self._helper_parseIperf(line)
            if throughput:
                sample = IperfSampleEvent(self.isServer, throughput)
                if self.isServer:
                    self.log.info('server side Throughput : ' + str(throughput))
                else:
                    self.log.info('client side Throughput : ' + str(throughput))
                sys.stdout.flush()
                self.module.send_event(sample)
                if self.stopAfterFirstReport:
                    break

        self.process.kill()


    def _helper_parseIperf(self, iperfOutput):
        """
        Parse iperf output and return bandwidth.
           iperfOutput: string
           returns: result string
        """
        import re

        r = r'([\d\.]+ \w+/sec)'
        m = re.findall(r, iperfOutput)
        if m:
            return m[-1]
        else:
            return None


class IperfModule(modules.ControlApplication):
    """
        Uniflex Iperf app listens to events to start iperf server/client and reports the throughput results using
        events.
    """

    def __init__(self):
        super(IperfModule, self).__init__()
        self.log = logging.getLogger('iperf_module.main')


    @modules.on_start()
    def start_iperf_module(self):
        self.log.debug("Start iperf module".format())


    @modules.on_exit()
    def stop_iperf_module(self):
        self.log.debug("Stop iperf module".format())


    @modules.on_event(IperfServerRequestEvent)
    def start_iperf_server(self, event):
        self.log.info('Function: start iperf server')
        self.log.info('args = %s' % str(event))

        try:
            appIsServer = event.isServer
            port = event.port
            protocol = event.protocol
            resultReportInterval = event.resultReportInterval
            stopAfterFirstReport = event.stopAfterFirstReport

            assert appIsServer

            # cmd = str("killall -9 iperf")
            # os.system(cmd);
            bind = event.bind

            cmd = ['/usr/bin/iperf', '-s']
            if protocol == "TCP":
                pass
            elif protocol == "UDP":
                cmd.extend(['-u'])

            if port:
                cmd.extend(['-p', str(port)])

            if bind:
                cmd.extend(['-B', str(bind)])

            if resultReportInterval:
                cmd.extend(['-i', str(resultReportInterval)])

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

            self._iperfServerScanner = ResultScanner(self, 'Server', stopAfterFirstReport, process)
            self._iperfServerScanner.start()

        except Exception as e:
            self.log.fatal("Install iperf server app failed: err_msg: %s" % (str(e)))


    #def stop_iperf_server(self):
    #    if self._iperfServerScanner:
    #        self._iperfServerScanner.stop()


    @modules.on_event(IperfClientRequestEvent)
    def start_iperf_client(self, event):
        self.log.info('Function: install iperf client')
        self.log.info('args = %s' % event.to_string())

        try:
            appIsServer = event.isServer
            port = event.port
            protocol = event.protocol
            resultReportInterval = event.resultReportInterval
            stopAfterFirstReport = event.stopAfterFirstReport

            assert not appIsServer

            self.log.info('Installing Client application')

            serverIp = event.destination
            udpBandwidth = event.udpBandwidth
            dualTest = event.dualtest
            dataToSend = event.dataToSend
            transmissionTime = event.transmissionTime
            self.log.info('1')

            cmd = ['/usr/bin/iperf', '-c', serverIp]

            if protocol == "TCP":
                pass
            elif protocol == "UDP":
                cmd.extend(['-u'])
                if udpBandwidth:
                    cmd.extend(['-b', str(udpBandwidth)])

            self.log.info('1')
            if port:
                cmd.extend(['-p', str(port)])

            self.log.info('1')
            if dualTest:
                cmd.extend(['-d'])

            self.log.info('1')
            if dataToSend:
                cmd.extend(['-n', str(dataToSend)])

            self.log.info('1')
            if transmissionTime:
                cmd.extend(['-t', str(transmissionTime)])

            self.log.info('1')
            if resultReportInterval:
                cmd.extend(['-i', str(resultReportInterval)])

            self.log.info('1')
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            self.log.info('1')

            self._iperfClientScanner = ResultScanner(self, 'Client', stopAfterFirstReport, process)
            self._iperfClientScanner.start()

        except Exception as e:
            self.log.fatal("Install iperf client app failed: err_msg: %s" % (str(e)))


    #def stop_iperf_client(self):
    #    if self._iperfClientScanner:
    #        self._iperfClientScanner.stop()
