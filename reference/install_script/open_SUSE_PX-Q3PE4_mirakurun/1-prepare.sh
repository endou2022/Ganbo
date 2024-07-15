# 前準備
#!/bin/bash

echo "YaST2で、docker , docker-compose , yast2-docker をインストール"
echo "YaST2で、docker 起動時実行、開始"
echo "ユーザーを docker のグループに入れる"

echo "YaST2で、基本的な開発 をインストール"
echo "YaST2で、dkms をインストール"

echo "YaST2で、pcsc-tools をインストール"
echo "YaST2で、pcsc-ccid  をインストール"
# opensc は保留

echo "reboot する"

sudo reboot