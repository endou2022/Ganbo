#!/bin/bash
echo "@link https://evafreak.com/ubuntu-tv-mirakurun-setting/"
echo "必要そうなソフトをインストール"
# mkdir ~/git
sudo zypper install dkms git         # git
sudo zypper install docker           # docker
sudo zypper install docker-compose   # docker-compose
sudo usermod -aG docker $USER        # 現在のユーザーをDockerグループに入れます
sudo systemctl enable docker
sudo systemctl start docker
echo "@link https://nyanonon.hatenablog.com/entry/20190909/1568040000"
sudo zypper install dvb-utils
sudo zypper install curl
read -p "リブートして変更を反映させる Hit enter: "
sudo reboot
