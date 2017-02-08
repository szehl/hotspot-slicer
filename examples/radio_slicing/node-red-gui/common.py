import sys
import logging
import subprocess

from uniflex.core import events
from uniflex.core.common import UniFlexThread

__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2016, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz}@tkn.tu-berlin.de"


class IperfClientProcess(UniFlexThread):
    """
        Thread scanning for throughput results.
    """
    def __init__(self, module, hostname, destIp):
        super().__init__(module)
        self.log = logging.getLogger()
        self.hostname = hostname
        self.destIp = destIp
        self.process = None
        self.nicer = []
        self.nicerSize = 5
        self.nicerIter = 0

    def task(self):
        self.log.debug('started scanner for iperf')
        cmd = "/usr/bin/iperf -c {} -f m -t 1000 -i 2".format(self.destIp)
        #cmd = "pwd"
        self.process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)

        while not self.is_stopped():
            line = self.process.stdout.readline()
            line = line.decode('utf-8')
            if line:
                if "failed" in line:
                    break
                throughput = self._helper_parseIperf(line)
                if throughput:
                    #numbers = [int(s) for s in throughput.split() if s.isdigit()]
                    numbers = throughput.split()
                    #print(throughput)
                    #print(numbers)
                    throughput = float(numbers[0])
                    self.log.debug('Throughput: {} MBps'.format(throughput))
                    sys.stdout.flush()
                    if len(self.nicer) < self.nicerSize:
                        self.nicer.append(throughput)
                    elif len(self.nicer) == self.nicerSize:
                        if self.nicerIter == self.nicerSize:
                            self.nicer[0] = throughput
                            self.nicerIter = 0
                        else:    			 
                            self.nicer[self.nicerIter] = throughput
                            self.nicerIter = self.nicerIter +1
                    nicerThroughput = sum(self.nicer)/len(self.nicer)	
                    self.log.debug('Throughput Nicer List: {} (MBps)'.format(self.nicer))	
                    self.log.debug('Throughput Nicer: {} MBps'.format(nicerThroughput))					
                    staThEvent = StaThroughputEvent(self.hostname, nicerThroughput)
                    self.module.send_event(staThEvent)
                    staPhREvent = StaPhyRateEvent(self.hostname, 54)
                    self.module.send_event(staPhREvent)

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


class StaInfo(object):
    def __init__(self, name, mac, ip):
        super().__init__()
        self.name = name
        self.mac = mac
        self.ip = ip
        self.state = False
        self.iperfProcess = None


class HostStateEvent(events.EventBase):
    def __init__(self, ip, state):
        super().__init__()
        self.ip = ip
        self.state = state

    def serialize(self):
        return {"ip": self.ip, "state": self.state}

    @classmethod
    def parse(cls, buf):
        sta = buf.get("sta", None)
        state = buf.get("state", None)
        return cls(sta, state)


class StaStateEvent(events.EventBase):
    def __init__(self, sta, state):
        super().__init__()
        self.sta = sta
        self.state = state

    def serialize(self):
        return {"sta": self.sta, "state": self.state}

    @classmethod
    def parse(cls, buf):
        sta = buf.get("sta", None)
        state = buf.get("state", None)
        return cls(sta, state)


class StaThroughputEvent(events.EventBase):
    def __init__(self, sta, throughput):
        super().__init__()
        self.sta = sta
        self.throughput = throughput

    def serialize(self):
        return {"sta": self.sta, "throughput": self.throughput}

    @classmethod
    def parse(cls, buf):
        sta = buf.get("sta", None)
        throughput = buf.get("throughput", None)
        return cls(sta, throughput)


class StaThroughputConfigEvent(events.EventBase):
    def __init__(self, sta, throughput):
        super().__init__()
        self.sta = sta
        self.throughput = throughput

    def serialize(self):
        return {"sta": self.sta, "throughput": self.throughput}

    @classmethod
    def parse(cls, buf):
        sta = buf.get("sta", None)
        throughput = buf.get("throughput", None)
        return cls(sta, throughput)


class StaPhyRateEvent(events.EventBase):
    def __init__(self, sta, phyRate):
        super().__init__()
        self.sta = sta
        self.phyRate = phyRate

    def serialize(self):
        return {"sta": self.sta, "phyRate": self.phyRate}

    @classmethod
    def parse(cls, buf):
        sta = buf.get("sta", None)
        phyRate = buf.get("phyRate", None)
        return cls(sta, phyRate)


class StaSlotShareEvent(events.EventBase):
    def __init__(self, sta, slotShare):
        super().__init__()
        self.sta = sta
        self.slotShare = slotShare

    def serialize(self):
        return {"sta": self.sta, "slotShare": self.slotShare}

    @classmethod
    def parse(cls, buf):
        sta = buf.get("sta", None)
        slotShare = buf.get("slotShare", None)
        return cls(sta, slotShare)
