import logging
import datetime
import time
from random import randint
from uniflex.core import modules

__author__ = "Anatolij Zubow"
__copyright__ = "Copyright (c) 2016, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{zubow}@tkn.tu-berlin.de"

'''
Local test of WiFi component.

sudo ../../../dev/bin/uniflex-agent --config config_local.yaml
'''


class WifiTestController(modules.ControlApplication):
    def __init__(self):
        super(WifiTestController, self).__init__()
        self.log = logging.getLogger('WifiTestController')

    @modules.on_start()
    def my_start_function(self):
        self.log.info("start wifi test")

        try:
            node = self.localNode
            self.log.info(node)
            device = node.get_device(0)
            self.log.info(device)

            iface = 'wlp3s0'

            cinfo = device.get_info(iface)
            self.log.info('WIFI::get_info %s' % cinfo)

            wi_mode = device.get_wifi_mode(iface)
            self.log.info('WIFI::get_wifi_mode %s' % wi_mode)

            curr_pwr = device.get_tx_power(iface)
            self.log.info('WIFI::get_power %d' % curr_pwr)

            new_pwr = randint(1, 17)
            self.log.info('WIFI::set_power to %d' % new_pwr)
            curr_pwr = device.set_tx_power(new_pwr, iface)

            time.sleep(0.5)

            curr_pwr = device.get_tx_power(iface)
            self.log.info('WIFI::get_power %d' % curr_pwr)

        except Exception as e:
            self.log.error("{} Failed, err_msg: {}"
                           .format(datetime.datetime.now(), e))

        self.log.info('... done')

    @modules.on_exit()
    def my_stop_function(self):
        self.log.info("stop wifi test")
