#!/bin/bash
# Run this before you save the image
# Version 1.0 Edited by James  - 7/28/2014

# Fix apt stuff
apt-get clean
apt-get update

# Root user stuff to clean
CLEAN_ROOT="/root/.ssh /root/.viminfo /root/.lesshst /root/.bash_history"

# Tmp stuff to clean
CLEAN_TMP="/tmp/* /var/tmp/*"

# We do not want documentation on our baselines
CLEAN_DOC="/usr/doc/* /usr/share/doc/*"

# Udev data to clean. Udev likes keeps interface names persistent accross bootups. We
# do not want that behaviour  because we move the image to different hardware 
# so we remove the saved rules and the generator rules
CLEAN_UDEV="/etc/udev/rules.d/70-persistent-net.rules"

#Dump old logs
CLEAN_LOGS="/var/log/*"

# Detel all the data we want gone
CLEAN="$CLEAN_TMP $CLEAN_DOC $CLEAN_UDEV $CLEAN_ROOT"
rm -rf $CLEAN

#log clean up fix
find /var/log -type f -regex ".*\.gz$"  -delete
find /var/log -type f -regex ".*\.[0-9]$" -delete
find /var/log -type f -exec  cp /dev/null  {} \;

# Old logs
rm /etc/hostname
history -c

#Prevent Udev from makeing persistent rules:
ln -s /dev/null /etc/udev/rules.d/70-persistent-net.rules

#make sure there are no rogue Name resloutions in /etc/hosts
ruby -i.bak -ne 'print if not /node\d-\d.*orbit/' /etc/hosts

poweroff
