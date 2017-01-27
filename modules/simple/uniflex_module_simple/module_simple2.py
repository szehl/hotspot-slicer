import logging
import random

from .module_simple import SimpleModule

__author__ = "Piotr Gawlowicz"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz}@tkn.tu-berlin.de"


class SimpleModule2(SimpleModule):
    def __init__(self):
        super(SimpleModule2, self).__init__()
        self.log = logging.getLogger('SimpleModule2')
        self.channel = 1
        self.power = 1

    def set_tx_power(self, power, iface):
        self.log.debug(("SimpleModule2 sets power: {}" +
                       "on device: {} and iface: {}")
                       .format(power, self.device, iface))
        self.power = power
        return {"SET_TX_POWER_OK_value": power}

    def get_tx_power(self, iface):
        self.log.debug("SimpleModule2 gets TX power on device: {}"
                       .format(self.device))
        return self.power

    def get_noise(self):
        self.log.debug("Get Noise".format())
        return random.randint(-120, -30)

    def get_airtime_utilization(self):
        self.log.debug("Get Airtime Utilization".format())
        return None

    def set_mac_access_parameters(self, queueId, queueParams):
        self.log.debug("SimpleModule2 sets EDCA parameters "
                       "for queue: {} on device: {}"
                       .format(queueId, self.device))

        print("Setting EDCA parameters for queue: {}".format(queueId))
        print("AIFS: {}".format(queueParams.getAifs()))
        print("CwMin: {}".format(queueParams.getCwMin()))
        print("CwMax: {}".format(queueParams.getCwMax()))
        print("TxOp: {}".format(queueParams.getTxOp()))
        return 0
