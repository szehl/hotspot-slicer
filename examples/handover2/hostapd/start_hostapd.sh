#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No arguments supplied; usage: $0 <channel>"
    exit 0
fi

CH=$1

echo "->Killing hostapd..."
sudo killall hostapd 2> /dev/null

sleep 1
echo "->Stopping network manager, stopping rfkill"
sudo service network-manager stop 2> /dev/null
sleep 1
sudo rfkill unblock all 2> /dev/null
sleep 1

echo "->Removing existing ifaces"
#iw dev wlan0 del
sudo iw dev wlan0 del 2> /dev/null
sudo iw dev wlan1 del 2> /dev/null
sudo iw dev ap1 del 2> /dev/null
sudo iw dev inject1 del 2> /dev/null
sudo iw dev wlan3 del 2> /dev/null
sleep 1

sleep 1

echo "->Creating interface ap1 on phy0..."
sudo iw phy phy0 interface add ap1 type managed
sleep 1
sudo ifconfig ap1 up

sudo ip addr add 192.168.5.1/24 dev ap1
sudo ifconfig ap1 txqueuelen 1
sudo ifconfig eth0 txqueuelen 1

sleep 1
sudo iw phy phy0 interface add inject1 type monitor
sleep 1
sudo ifconfig inject1 up
sleep 1
echo "Exting ARP cache hold time..."
echo 3600 | sudo tee /proc/sys/net/ipv4/neigh/default/gc_stale_time
sleep 1
echo "Starting hapd..."

sudo hostapd ./hostapd-config/hostapd-ch${CH}.conf


