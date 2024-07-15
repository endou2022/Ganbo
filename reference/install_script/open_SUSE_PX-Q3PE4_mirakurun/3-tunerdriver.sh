#!/bin/bash

# @link https://www.digital-den.jp/simplelife/archives/7655/2023%E5%B9%B48%E6%9C%88%E7%89%88-45%E5%88%86%E3%81%A7%E4%BD%9C%E3%82%8C%E3%82%8B%E8%87%AA%E5%AE%85%E9%8C%B2%E7%94%BB%E3%82%B5%E3%83%BC%E3%83%90%E3%83%BC%EF%BC%88ubuntu-22-04-3lts/

mkdir ~/git
cd ~/git
#git clone https://github.com/nns779/px4_drv
#kernel 6.4以降
# @link https://blog.tsukumijima.net/article/px4_drv-dkms-error/
git clone https://github.com/tsukumijima/px4_drv
cd px4_drv/fwtool/
make
wget http://plex-net.co.jp/plex/pxw3u4/pxw3u4_BDA_ver1x64.zip -O pxw3u4_BDA_ver1x64.zip
unzip -oj pxw3u4_BDA_ver1x64.zip pxw3u4_BDA_ver1x64/PXW3U4.sys
./fwtool PXW3U4.sys it930x-firmware.bin
sudo mkdir -p /lib/firmware
sudo cp it930x-firmware.bin /lib/firmware/
cd ../
sudo cp -a ./ /usr/src/px4_drv-0.2.1
sudo dkms add px4_drv/0.2.1
sudo dkms install px4_drv/0.2.1
echo "再起動後 ls -l /dev/px* でドラウバー確認"
read -p "ドライバがインストールされました。enterキーを押すとリブートします。"
sudo reboot
