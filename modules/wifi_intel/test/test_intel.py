#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import uniflex_module_wifi_intel
import pickle

'''
    Direct module test; without framework.
    Req.: Intel WiFi
'''
if __name__ == '__main__':

    wifi = uniflex_module_wifi_intel.Iwl5300Module()

    wifi.my_start_function()

    samples = 100
    csi = wifi.get_csi(samples, False)

    print(csi.shape)

    filehandler = open("csi_small.obj","wb")
    pickle.dump(csi, filehandler, protocol=0)
    filehandler.close()

    wifi.my_stop_function()
