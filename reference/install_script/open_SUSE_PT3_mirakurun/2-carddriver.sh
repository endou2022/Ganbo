#!/bin/bash
echo "@link https://evafreak.com/ubuntu-tv-mirakurun-setting/"
echo "カードリーダのインストールとその確認"
sudo zypper install pcsc-tools pcsc-ccid
read -p "リブートして変更を反映させる Hit enter: "
sudo reboot

