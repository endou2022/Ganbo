#!/bin/bash
pcsc_scan 

echo "@link https://evafreak.com/ubuntu-tv-mirakurun-setting/"
echo "Docker環境ではホストマシンのpcscdを停⽌します"
sudo systemctl stop pcscd
sudo systemctl disable pcscd
sudo systemctl status pcscd
read -p "リブートして変更を反映させる Hit enter: "
sudo reboot