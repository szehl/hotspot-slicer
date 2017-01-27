import os
import logging
import inspect
import subprocess

from uniflex.core import exceptions
from uniflex.core import modules

__author__ = "Piotr Gawlowicz, Anatolij Zubow"
__copyright__ = "Copyright (c) 2015, Technische Universität Berlin"
__version__ = "0.1.0"
__email__ = "{gawlowicz, zubow}@tkn.tu-berlin.de"

"""
Implementation of UPI_R and UPI_N interfaces for the R&S signal generator.
"""


class RsSignalGenModule(modules.DeviceModule):
    def __init__(self):
        super(RsSignalGenModule, self).__init__()
        self.log = logging.getLogger('RsSignalGenModule')

    def play_waveform(self, iface, freq, power_lvl, **kwargs):
        self.log.debug('playWaveform()')

        try:
            # set the center frequency
            exec_file = 'rs_siggen_etherraw'
            args = iface + ' \"FREQ ' + freq + 'MHz\"'

            command = exec_file + ' ' + args
            self.log.debug('playWaveform on iface %s ... set frequency' % (iface))
            self.log.info('exec %s' % command)

            [rcode, sout, serr] = self._run_command(command)

            # set power level
            args = iface + ' \":POW ' + str(power_lvl) + '\"'

            command = exec_file + ' ' + args
            self.log.debug('playWaveform on iface %s ... set power level to %s' % (iface, str(power_lvl)))
            self.log.info('exec %s' % command)

            [rcode, sout, serr] = self._run_command(command)

            # power on
            args = iface + ' \"OUTP ON\"'

            command = exec_file + ' ' + args
            self.log.debug('playWaveform on iface %s ... power on' % (iface))
            self.log.info('exec %s' % command)

            [rcode, sout, serr] = self._run_command(command)

            return True
        except Exception as e:
            self.log.fatal("Failed to play waveform, err_msg:%s" % (str(e)))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to play waveform: ' + str(e))

    def stop_waveform(self, iface, **kwargs):
        self.log.debug('stopWaveform()')

        try:
            exec_file = str(os.path.join(self.getPlatformPath())) + '/rs_siggen_etherraw'
            # power off
            args = iface + '\"OUTP OFF\"'

            command = exec_file + ' ' + args
            self.log.debug('stopWaveform on iface %s ... power off' % (iface))
            self.log.debug('exec %s' % command)

            [rcode, sout, serr] = self._run_command(command)

            return True
        except Exception as e:
            self.log.fatal("Failed to stop waveform, err_msg:%s" % (str(e)))
            raise exceptions.FunctionExecutionFailedException(
                func_name=inspect.currentframe().f_code.co_name,
                err_msg='Failed to stop waveform: ' + str(e))

    def _run_command(self, command):
        """
            Method to start the shell commands and get the output as iterater object
        """

        sp = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = sp.communicate()

        if False:
            if out:
                self.log.debug("standard output of subprocess:")
                self.log.debug(out)
            if err:
                self.log.debug("standard error of subprocess:")
                self.log.debug(err)

        if err:
            raise Exception("An error occurred in RsSignalGenModule: %s" % err)

        return [sp.returncode, out.decode("utf-8"), err.decode("utf-8")]
