#!/bin/bash

killall -9 node-red
killall -9 hostapd
killall -9 wpa_supplicant
killall -9 uniflex-agent
killall -9 hmac_userspace_daemon
killall -9 iperf
#sleep 5
#modprobe -r ath9k ath mac80211 cfg80211 ip_tables ip6_tables x_tables rfcomm ath9k_common ath9k_hw
#sleep 5
