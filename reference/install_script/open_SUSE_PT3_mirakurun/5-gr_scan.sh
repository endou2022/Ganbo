#!/bin/bash
echo "@link https://evafreak.com/ubuntu-tv-mirakurun-setting/"
echo "地デジチャンネルスキャン"
curl -X PUT "http://localhost:40772/api/config/channels/scan?type=GR&setDisabledOnAdd=false&refresh=true"
