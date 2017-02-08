#!/usr/bin/env bash

export PATH=$PATH:/root/slicer/hmac/ath9k-hmac/hmac_userspace_daemon/
sleep 1
uniflex-agent --config config_local.yaml
