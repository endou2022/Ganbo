FROM nikolaik/python-nodejs:python3.12-nodejs21-bullseye
# Debianにpythonとnode.js(npm)をインストールしたイメージを使う

WORKDIR /app

#localeを日本語にする
# https://qiita.com/valzer0/items/db7639d8231bf5121297 (2024/01/07)
# https://www.rcnp.osaka-u.ac.jp/~kobayash/be_koba/mem/debian.html (2024/01/07)
RUN apt-get update && apt-get install -y locales 
RUN echo "ja_JP.UTF-8 UTF-8" >> /etc/locale.gen && locale-gen && update-locale LANG=ja_JP.UTF-8

#TimeZoneをJSTにする
# https://zenn.dev/mtmatma/articles/7d561577f1fc46 (2024/01/07)
#RUN ln -sf /usr/share/zoneinfo/Japan /etc/localtime

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

RUN npm install rivarun -g

RUN mkdir /mnt/ts
RUN chmod a+w /mnt/ts

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
