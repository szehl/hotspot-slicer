#!/bin/bash

iperf -c 192.168.6.10 -t30 &
iperf -c 192.168.6.30 -t30 &
iperf -c 192.168.6.11 -t30 &
