#!/bin/bash
echo "チャンネルスキャン CS"
curl -X PUT "http://localhost:40772/api/config/channels/scan?type=CS&setDisabledOnAdd=false&refresh=true"
