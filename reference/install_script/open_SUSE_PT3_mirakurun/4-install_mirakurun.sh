#!/bin/bash
echo "ホームディレクトリに戻る"
cd
echo "@link https://evafreak.com/ubuntu-tv-mirakurun-setting/"
echo "Mirakurunをインストール"
curl -sf https://raw.githubusercontent.com/l3tnun/docker-mirakurun-epgstation/v2/setup.sh | sh -s
cd docker-mirakurun-epgstation
docker-compose pull
docker-compose run --rm -e SETUP=true mirakurun
docker-compose up -d  # mirakurun起動
