#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No arguments supplied; usage: $0 <phy>"
    exit 0
fi

phy=$1
randip=$(shuf -i 2-253 -n 1)

# cleanup
for i in `seq 0 10`;
do
  sudo iw dev mon${i} del 2>/dev/null
  sudo iw dev wlan${i} del 2>/dev/null
  sudo iw dev sta${i} del 2>/dev/null
  sudo iw dev ap${i} del 2>/dev/null
done

sudo rfkill unblock all 2>/dev/null

#Configuring AP
sleep 1
sudo killall -9 wpa_supplicant 2> /dev/null
sleep 1
sudo iw phy ${phy} interface add sta1 type managed
sleep 1
sudo ip link set dev sta1 address 00:15:6d:84:3c:ec
sleep 1
sudo ifconfig sta1 192.168.6.20 netmask 255.255.255.0
sleep 1
sudo service network-manager stop /dev/null
sleep 1
sudo ifconfig sta1 up
sleep 1
wpa_supplicant -Dnl80211 -ista1 -c/root/wpa_supplicant_home.conf &
sleep 2
iperf -s &
