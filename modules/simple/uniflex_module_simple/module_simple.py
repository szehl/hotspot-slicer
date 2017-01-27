import time
import logging
import random

from sbi.wifi.net_device import WiFiNetDevice
from sbi.wifi.events import PacketLossEvent, SpectralScanSampleEvent

from uniflex.core import modules
from uniflex.core import exceptions
from uniflex.core.common import UniFlexThread

__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz}@tkn.tu-berlin.de"


class SpectralScanner(UniFlexThread):
    """docstring for SpectralScanner"""

    def __init__(self, module):
        super().__init__(module)

    def task(self):
        while not self.is_stopped():
            self.module.log.info("Spectral scan sample")
            sample = SpectralScanSampleEvent(
                sample=random.uniform(0, 64))
            self.module.send_event(sample)
            time.sleep(1)


class PacketLossMonitor(UniFlexThread):
    """docstring for SpectralScanner"""

    def __init__(self, module):
        super().__init__(module)

    def task(self):
        while not self.is_stopped():
            self.module.log.debug("Packet Lost")
            event = PacketLossEvent()
            # yeld or send Event to controller
            self.module.send_event(event)
            time.sleep(random.uniform(0, 10))


class SimpleModule(modules.DeviceModule, WiFiNetDevice):
    def __init__(self):
        super(SimpleModule, self).__init__()
        self.log = logging.getLogger('SimpleModule')
        self.channel = 1
        self.power = 1

        self.stopRssi = True

        self._packetLossMonitor = PacketLossMonitor(self)
        self._spectralScanner = SpectralScanner(self)

    @modules.on_start()
    def _myFunc_1(self):
        self.log.info("This function is executed on agent start".format())

    @modules.on_exit()
    def _myFunc_2(self):
        self.log.info("This function is executed on agent exit".format())

    @modules.on_connected()
    def _myFunc_3(self):
        self.log.info("This function is executed on connection"
                      " to global controller".format())

    @modules.on_disconnected()
    def _myFunc_4(self):
        self.log.info(
            "This function is executed after connection with global"
            " controller was lost".format())

    @modules.on_first_call_to_module()
    def _myFunc_5(self):
        self.log.info(
            "This function is executed before first UPI"
            " call to module".format())

    def _before_set_channel(self):
        self.log.info("This function is executed before set_channel".format())

    def _after_set_channel(self):
        self.log.info("This function is executed after set_channel".format())

    @modules.before_call(_before_set_channel)
    @modules.after_call(_after_set_channel)
    def set_channel(self, channel, iface):
        self.log.info(("Simple Module sets channel: {} " +
                       "on device: {} and iface: {}")
                      .format(channel, self.device, iface))
        self.channel = channel
        return ["SET_CHANNEL_OK", channel, 0]

    def get_channel(self, iface):
        self.log.debug(
            "Simple Module gets channel of device: {} and iface: {}"
            .format(self.device, iface))
        return self.channel

    def set_tx_power(self, power, iface):
        self.log.debug("Set power: {} on device: {} and iface: {}"
                       .format(power, self.device, iface))
        self.power = power
        return {"SET_TX_POWER_OK_value": power}

    def get_tx_power(self, iface):
        self.log.debug(
            "Simple Module gets TX power on device: {} and iface: {}"
            .format(self.device, iface))
        return self.power

    def packet_loss_monitor_start(self):
        if self._packetLossMonitor.is_running():
            return True

        self.log.info("Start Packet Loss Monitor")
        self._packetLossMonitor.start()
        return True

    def packet_loss_monitor_stop(self):
        self.log.info("Stop Packet Loss Monitor")
        self._packetLossMonitor.stop()
        return True

    def is_packet_loss_monitor_running(self):
        return self._packetLossMonitor.is_running()

    def spectral_scan_start(self):
        if self._spectralScanner.is_running():
            return True

        self.log.info("Start spectral scanner")
        self._spectralScanner.start()
        return True

    def spectral_scan_stop(self):
        self.log.info("Stop spectral scanner")
        self._spectralScanner.stop()
        return True

    def is_spectral_scan_running(self):
        return self._spectralScanner.is_running()

    def clean_per_flow_tx_power_table(self, iface):
        self.log.debug("clean per flow tx power table".format())
        raise exceptions.FunctionExecutionFailedException(
            func_name='radio.clean_per_flow_tx_power_table', err_msg='wrong')
