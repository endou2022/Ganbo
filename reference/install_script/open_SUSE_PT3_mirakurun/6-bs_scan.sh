#!/bin/bash
echo "@link https://evafreak.com/ubuntu-tv-mirakurun-setting/"
echo "BSチャンネルスキャン"
curl -X PUT "http://localhost:40772/api/config/channels/scan?type=BS&setDisabledOnAdd=false&refresh=true"
