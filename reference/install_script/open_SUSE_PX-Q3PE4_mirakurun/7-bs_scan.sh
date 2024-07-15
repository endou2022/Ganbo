#!/bin/bash
echo "チャンネルスキャン BS"
curl -X PUT "http://localhost:40772/api/config/channels/scan?type=BS&setDisabledOnAdd=false&refresh=true"