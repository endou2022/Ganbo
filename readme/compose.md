# compose.yml のカスタマイズ

```docker compose build```コマンドを実施する前に  compose.yml  をインストールする環境に合わせて書き換えてください。<br>

compose.yml  の内容と変更する場所
```
version: '3'

services:
  fastapi:
    build:
      context: "./fastapi"
      dockerfile: "Dockerfile"
    container_name: ganbo_fastapi
    restart: always
    depends_on:
      - mariadb
    ports:
      - 2595:8000		# ポート番号2595が他と重なる場合は変更してください
    volumes:
      - ./fastapi/app:/app
# 動画ファイルの保存場所指定。必須の変更項目
# D:\TS 、または、 /mnt/ts(ホスト側のディレクトリ) を環境に合わせて変更
# どちらかを # でコメントアウトする
#      - D:\TS:/mnt/ts		# Windowsの場合の例
      - /mnt/ts:/mnt/ts	# Linuxの場合の例。パーミッションはすべてのユーザーが読み書き可能とする。
    environment:
      - TZ=Asia/Tokyo
      - ENVIRON
    logging:
      driver: json-file
      options:
        max-file: "1"
        max-size: 10m

  mariadb:
    build:
      context: ./mariadb
      dockerfile: Dockerfile
    container_name: ganbo_mariadb
    restart: always
    volumes:
      - "./mariadb/initdb.d:/docker-entrypoint-initdb.d"
    environment:
      - MYSQL_ROOT_PASSWORD=root
      - MYSQL_DATABASE=ganbo
      - MYSQL_USER=ganbo
      - MYSQL_PASSWORD=ganbo
      - TZ=Asia/Tokyo
    logging:
      driver: json-file
      options:
        max-file: "1"
        max-size: 10m

# データベースの中身を見たい人は、下記の # をすべて消す
# ポート番号 4000 でphpmyadminにアクセスできる
#  phpmyadmin:
#    build:
#      context: ./phpmyadmin
#      dockerfile: Dockerfile
#    container_name: ganbo_phpmyadmin
#    restart: always
#    environment:
#      - PMA_ARBITRARY=1
#      - PMA_HOST=mariadb
#      - PMA_USER=root
#      - PMA_PASSWORD=root
#      - TZ=Asia/Tokyo
#    depends_on:
#      - mariadb
#    ports:
#      - 4000:80
#    logging:
#      driver: json-file
#      options:
#        max-file: "1"
#        max-size: 10m
```
