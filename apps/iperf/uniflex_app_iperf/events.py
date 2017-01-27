from uniflex.core import events

__author__ = "Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universitat Berlin"
__version__ = "0.1.0"
__email__ = "{zubow}@tkn.tu-berlin.de"


class IperfRequestEvent(events.EventBase):
    """
        Base class for all IperfReqEvents
    """
    def __init__(self, startTime=0, isServer=True, resultReportInterval=None, stopAfterFirstReport=True, port=5001, protocol='TCP', tcpWindow=None):
        """
        Events consumed by iperf app.
        :param startTime: when to start
        :param isServer: whether to start iperf server
        :param resultReportInterval: how often to report throughput values
        :param stopAfterFirstReport: whether to stop after getting the first result
        :param port: IP port
        :param protocol: 'TCP', 'UDP', ...
        :param tcpWindow: TCP windows size
        """
        super().__init__()
        self.startTime = startTime
        self.isServer = isServer
        self.resultReportInterval = resultReportInterval
        self.stopAfterFirstReport = stopAfterFirstReport
        self.port = port
        self.protocol = protocol
        self.tcpWindow = tcpWindow

    def to_string(self):
        return 'tbd'


class IperfServerRequestEvent(IperfRequestEvent):
    def __init__(self, startTime=0, resultReportInterval=None, stopAfterFirstReport=True, port=5001, protocol='TCP',
                 tcpWindow=None, bind=None):
        """
        Events consumed by iperf app to start iperf server.
        :param startTime: when to start
        :param resultReportInterval: how often to report throughput values
        :param stopAfterFirstReport: whether to stop after getting the first result
        :param port: IP port
        :param protocol: 'TCP', 'UDP', ...
        :param tcpWindow: TCP windows size
        :param bind: ip address to bind to
        """
        super().__init__(startTime, True, resultReportInterval, stopAfterFirstReport, port, protocol, tcpWindow)
        self.bind = bind


class IperfClientRequestEvent(IperfRequestEvent):
    def __init__(self, startTime=0, resultReportInterval=None, stopAfterFirstReport=True, port=5001, protocol='TCP',
                 tcpWindow=None, destination=None, udpBandwidth = '1M', dualtest = False, dataToSend = None,
                 transmissionTime = None, frameLen = None):
        """
        Events consumed by iperf app to start iperf client.
        :param startTime: when to start
        :param resultReportInterval: how often to report throughput values
        :param stopAfterFirstReport: whether to stop after getting the first result
        :param port: IP port
        :param protocol: 'TCP', 'UDP', ...
        :param tcpWindow: TCP windows size
        :param destination: ip address of server to connect to
        :param udpBandwidth: bandwidth in case of UDP
        :param dualtest: run dual test
        :param dataToSend: data to be send
        :param transmissionTime: how long to run iperf client
        :param frameLen: length of the frame
        """
        super().__init__(startTime, False, resultReportInterval, stopAfterFirstReport, port, protocol, tcpWindow)
        self.destination = destination
        self.udpBandwidth = udpBandwidth
        self.dualtest = dualtest
        self.dataToSend = dataToSend
        self.transmissionTime = transmissionTime
        self.frameLen = frameLen


class IperfSampleEvent(events.EventBase):
    """
        After iperf app was started it starts sending measurement results (throughput) via this events.
    """
    def __init__(self, isServer, throughput):
        """
        Iperf sample result event.
        :param isServer: results comming from iperf server or client
        :param throughput: the measured throughput value
        """
        super().__init__()
        self.isServer = isServer
        self.throughput = throughput
