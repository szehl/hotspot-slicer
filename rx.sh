#/bin/bash

ch=1
brate=6

./tx_diversity/init_wifi.sh ${ch}
./tx_diversity/init_wifi_intel.sh ${ch}

./tx_diversity/set_bitrate.sh ${brate} 0
./tx_diversity/set_bitrate.sh ${brate} 1

python ./tx_diversity/set_mac_addr.py
