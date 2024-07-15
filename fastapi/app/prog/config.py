# -*- coding: utf-8 -*-

#---------------------------------------------------------------------------
# 定数 (python に定数という概念はないが)
#---------------------------------------------------------------------------
__soft_name__   = 'Ganbo'
__version__     = '1.0'
__description__ = 'テレビチューナーサーバー mirakurun のクライアント'
__copyright__   = '(C)Copyright 2024 Y.Endou All rights reserved.'
software        = f"{__soft_name__} {__version__}"
footer_str      = f"{__soft_name__} {__version__} : {__description__} {__copyright__}"
#---------------------------------------------------------------------------
# データベースへの接続パラメータ
# conn = mydb.connect(**config.database) として使う
# STRICT_TRANS_TABLES(厳密モード)をはずして、超過文字を入力したときにエラーを出さない（超過分切り捨て）ようにしている
database = {"host" : 'mariadb' ,	# データベースのアドレス dockerなので、IPアドレスではない
			"port" : '3306' ,		# MySQL(mariadb)のポート番号 compose.yml で設定
			"user" : 'ganbo' ,
			"password" : 'ganbo' ,
			"database" : 'ganbo',
			"sql_mode" : 'ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION'}
#---------------------------------------------------------------------------
# 共通変数
# import config と読み込んで
# config.変数名でアクセスする
# https://qiita.com/minidaruma/items/11eafc95855c007335f6 (2024/02/26)
# global では別ファイルのグローバル変数を参照することはできない
#---------------------------------------------------------------------------
rec_task_list  = {}		# 録画タスククラスの辞書 主にg94.pyで利用
save_root      = ""		# 保存ルートディレクトリ。以下スタートアップ時にデータベースの値で書き換える
save_macro     = ""		# 保存ファイル名(マクロ)
mirakurun_ip   = ""		# mirakurun IP アドレス
mirakurun_port = ""		# mirakurun ポート番号
#---------------------------------------------------------------------------
