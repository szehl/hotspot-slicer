#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No arguments supplied; usage: $0 <phy>"
    exit 0
fi

phy=$1

# cleanup
for i in `seq 0 10`;
do
  sudo iw dev mon${i} del 2>/dev/null
  sudo iw dev wlan${i} del 2>/dev/null
  sudo iw dev wifi${i} del 2>/dev/null
  sudo iw dev ap${i} del 2>/dev/null
  sudo iw dev sta${i} del 2>/dev/null
done
sudo iw dev wlan0_0 del

sudo rfkill unblock all 2>/dev/null

#Configuring AP
sleep 1
sudo killall -9 hostapd 2> /dev/null
sleep 1
sudo iw phy ${phy} interface add ap5 type managed
sleep 1
sudo ifconfig ap5 up
sleep 1
sudo ifconfig ap5 down
sleep 1
sudo ip link set dev ap5 address 00:15:6d:86:0f:18
sleep 1
sudo ifconfig ap5 192.168.6.1 netmask 255.255.255.0
sleep 1
sudo service network-manager stop 2>/dev/null
sleep 1
#./resfi/hostapd-20131120/hostapd/hostapd hostapd-multi-ssid.conf &
sudo hostapd hostapd-multi-ssid.conf &
sleep 5
sudo ifconfig wlan0_0 192.168.7.1 netmask 255.255.255.0
sudo iwconfig ap5 rate 54M
sudo iwconfig wlan0_0 rate 54M
