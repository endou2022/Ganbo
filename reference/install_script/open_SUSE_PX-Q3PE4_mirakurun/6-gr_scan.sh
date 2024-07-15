#!/bin/bash
echo "チャンネルスキャン 地デジ"
curl -X PUT "http://localhost:40772/api/config/channels/scan?type=GR&setDisabledOnAdd=false&refresh=true"
