import logging
import inspect
import subprocess

import matlab.engine
import numpy as np

from uniflex.core import modules
import uniflex_module_wifi
from uniflex.core import exceptions


__author__ = "Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{zubow}@tkn.tu-berlin.de"


"""
    WiFi module for Intel 5300 chipsets patched with the driver from
    http://dhalperi.github.io/linux-80211n-csitool/

    Note: this module requres the Matlab Python engine:
    https://de.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html
"""
class Iwl5300Module(uniflex_module_wifi.WifiModule):
    def __init__(self):
        super(Iwl5300Module, self).__init__()
        self.log = logging.getLogger('Iwl5300Module')


    @modules.on_start()
    def my_start_function(self):
        self.eng = matlab.engine.start_matlab()


    @modules.on_exit()
    def my_stop_function(self):
        self.eng.quit()


    def get_csi(self, num_samples, withMetaData=False):
        """
        Reads the next csi values.
        :param num_samples: the number of samples to read
        :return: for withMetaData=True: tbd ELSE: the csi values as numpy matrix of dimension: num_samples x Ntx x Nrx x Nsc
        """

        try:
            tempfile = '/tmp/out'

            # 1. userland netlink
            cmd = 'log_to_file_max ' + tempfile + ' ' + str(num_samples)
            [rcode, sout, serr] = self.run_command(cmd)

            # 2. read from file
            csi_trace = self.eng.read_bf_file(tempfile)

            num_samples = len(csi_trace)

            print('no. samples: %d' % num_samples)

            if withMetaData:
                all = []

                for s in range(num_samples):
                    csi_entry = csi_trace[s]
                    csi = self.eng.get_scaled_csi(csi_entry)
                    csi_np = np.zeros(csi.size, dtype=np.complex_)

                    for ii in range(csi.size[0]):
                        for jj in range(csi.size[1]):
                            for zz in range(csi.size[2]):
                                csi_np[ii][jj][zz] = csi[ii][jj][zz]

                    res = {}
                    res['csi_scaled'] = csi_np			
                    for k in csi_entry.keys():
                        res[k] = csi_entry[k]

                    all.append(res)
	
                return all

            else:
                Ntx = 3
                Nrx = 3
                Nsc = 30
                csi_np = np.zeros((num_samples, Ntx, Nrx, Nsc), dtype=np.complex_)

                for s in range(num_samples):
                    csi_entry = csi_trace[s]
                    csi = self.eng.get_scaled_csi(csi_entry)
                    for ii in range(csi.size[0]):
                        for jj in range(csi.size[1]):
                            for zz in range(csi.size[2]):
                                csi_np[s][ii][jj][zz] = csi[ii][jj][zz]

                return csi_np
        except Exception as e:
            self.log.fatal("Failed to get CSI: %s" % str(e))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to get CSI: ' + str(e))

        return None 
