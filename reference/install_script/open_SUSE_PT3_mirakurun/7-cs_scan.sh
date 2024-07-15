#!/bin/bash
echo "@link https://evafreak.com/ubuntu-tv-mirakurun-setting/"
echo "CSチャンネルスキャン"
curl -X PUT "http://localhost:40772/api/config/channels/scan?type=CS&setDisabledOnAdd=false&refresh=true"
