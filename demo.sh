#!/bin/bash

killall -9 wpa_supplicant
killall -9 scheduler
killall -9 hostapd
#sudo /etc/init.d/networking restart
#sleep 1
#echo "  8888888888888888888:::8::::::M::aAa::::::::M8888888888       8
#  88   8888888888::88::::8::::M:::::::::::::888888888888888 8888
# 88  88888888888:::8:::::::::M::::::::::;::88:88888888888888888
# 8  8888888888888:::::::::::M::"@@@@@@@"::::8w8888888888888888
#  88888888888:888::::::::::M:::::"@a@":::::M8i888888888888888
# 8888888888::::88:::::::::M88:::::::::::::M88z88888888888888888
#8888888888:::::8:::::::::M88888:::::::::MM888!888888888888888888
#888888888:::::8:::::::::M8888888MAmmmAMVMM888*88888888   88888888
#888888 M:::::::::::::::M888888888:::::::MM88888888888888   8888888
#8888   M::::::::::::::M88888888888::::::MM888888888888888    88888
# 888   M:::::::::::::M8888888888888M:::::mM888888888888888    8888
#  888  M::::::::::::M8888:888888888888::::m::Mm88888 888888   8888
#   88  M::::::::::::8888:88888888888888888::::::Mm8   88888   888
#   88  M::::::::::8888M::88888::888888888888:::::::Mm88888    88
#   8   MM::::::::8888M:::8888:::::888888888888::::::::Mm8     4
#       8M:::::::8888M:::::888:::::::88:::8888888::::::::Mm    2
#      88MM:::::8888M:::::::88::::::::8:::::888888:::M:::::M
#     8888M:::::888MM::::::::8:::::::::::M::::8888::::M::::M
#    88888M:::::88:M::::::::::8:::::::::::M:::8888::::::M::M
#   88 888MM:::888:M:::::::::::::::::::::::M:8888:::::::::M:
#   8 88888M:::88::M:::::::::::::::::::::::MM:88::::::::::::M
#     88888M:::88::M::::::::::*88*::::::::::M:88::::::::::::::M
#    888888M:::88::M:::::::::88@@88:::::::::M::88::::::::::::::M
#    888888MM::88::MM::::::::88@@88:::::::::M:::8::::::::::::::*8
#    88888  M:::8::MM:::::::::*88*::::::::::M:::::::::::::::::88@@
#    8888   MM::::::MM:::::::::::::::::::::MM:::::::::::::::::88@@
#     888    M:::::::MM:::::::::::::::::::MM::M::::::::::::::::*8
#     888    MM:::::::MMM::::::::::::::::MM:::MM:::::::::::::::M
#      88     M::::::::MMMM:::::::::::MMMM:::::MM::::::::::::MM
#      88    MM:::::::::MMMMMMMMMMMMMMM::::::::MMM::::::::MMM
#        88    MM::::::::::::MMMMMMM::::::::::::::MMMMMMMMMM
#              
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
cd /root/slicer/examples/radio_slicing/node-red-gui/
sleep 1
node-red gui.json &
sleep 1
uniflex-agent --config /root/slicer/examples/radio_slicing/node-red-gui/config.yaml &
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
