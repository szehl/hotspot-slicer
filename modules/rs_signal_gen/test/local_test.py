import logging
import datetime
import time
from uniflex.core import modules

__author__ = "Anatolij Zubow"
__copyright__ = "Copyright (c) 2016, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{zubow}@tkn.tu-berlin.de"

'''
Local test of R&S module.
'''


class RSController(modules.ControlApplication):
    def __init__(self):
        super(RSController, self).__init__()
        self.log = logging.getLogger('RSController')

    @modules.on_start()
    def my_start_function(self):
        self.log.info("start R&S test")

        try:
            node = self.localNode
            device = node.get_device(0)

            # IP address of remote R&S signal generator
            iface = "192.168.10.102"
            freq = 5200
            power_lvl = 10

            if device.radio.play_waveform(self, iface, freq, power_lvl):
                time.sleep(2)

                if device.radio.stop_waveform(self, iface):
                    self.log.info("Test OK")

        except Exception as e:
            self.log.error("{} Failed with control R&S signal generator, err_msg: {}"
                           .format(datetime.datetime.now(), e))
            raise e

        self.log.info('... done')

    @modules.on_exit()
    def my_stop_function(self):
        self.log.info("stop R&S test")
