#!/bin/bash

killall -9 wpa_supplicant
killall -9 scheduler
killall -9 hostapd

#             R A D I O ____ S L I C E R ____ D E M O
#             ***************************************
#                         DEBUG MODE
#                    !DO NOT USE IN PUBLIC!"
#
#modprobe ath9k ath mac80211 cfg80211 ip_tables ip6_tables x_tables rfcomm ath9k_common ath9k_hw
#sleep 5
echo "             
      R A D I O ____ S L I C E R ____ D E M O
      ***************************************
                     DEBUG MODE"
sleep 1      
echo "
      ***********************************
      Disconnecting all Client STAs from network
      ***********************************"
ssh -f robat@192.168.200.32 "sudo killall -9 wpa_supplicant; sudo ifconfig sta1 down"
ssh -f robat@192.168.200.43 "sudo ifconfig sta2 down; sudo killall -9 wpa_supplicant"
ssh -f robat@192.168.200.69 "sudo killall -9 wpa_supplicant; sudo ifconfig sta1 down"
sleep 5
echo "
      ***********************************
      Starting Node Red and Gui Feeder...
      ***********************************
"
sleep 1
cd /root/slicer/examples/radio_slicing/node_red_gui/
sleep 1
node-red gui.json &
sleep 1
uniflex-agent --config /root/slicer/examples/radio_slicing/node_red_gui/config.yaml &
sleep 1
cd ~
sleep 1
echo "
      ***********************************
      Starting AP...
      ***********************************"
sleep 1
/root/slicer/start_hmac_ap.sh phy0
sleep 1
echo "      
      ***********************************
      Starting Radio Slicer...
      ***********************************"
cd /root/slicer/examples/radio_slicing/
sleep 1
uniflex-agent --config /root/slicer/examples/radio_slicing/config_local.yaml &
sleep 1
echo "
      ***********************************
      Now connecting Home Client STA e.g. TV...
      ***********************************"
ssh -f robat@192.168.200.32 "/home/robat/slicer/start_wpa_supplicant_tv.sh phy0" 
sleep 1
echo "
      ***********************************
      Now Connecting 1st Guest STA...
      ***********************************"
ssh -f robat@192.168.200.69 "/home/robat/slicer/start_wpa_supplicant_guest1.sh phy1"
sleep 1
echo "
      ***********************************
      Now connecting 2nd Guest STA...
      ***********************************"
ssh -f robat@192.168.200.43 "/home/robat/slicer/start_wpa_supplicant_guest2.sh phy0"
echo "
      ***********************************
      Demo successfully started...
      ***********************************"
#sleep 200
#/root/slicer/demo_stop.sh
#sleep 5
#/root/slicer/demo.sh
