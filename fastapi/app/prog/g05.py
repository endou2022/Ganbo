# -*- coding: utf-8 -*-

#---------------------------------------------------------------------------
# 「自動予約一覧」ルーチン
#---------------------------------------------------------------------------
from jinja2 import Environment, FileSystemLoader
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import mysql.connector as mydb
from prog import g91 , g92 , g94 , config

env_j2 = Environment(loader=FileSystemLoader('./templates'))

router = APIRouter(tags=['自動予約一覧'])
# --------------------------------------------------
@router.get('/automatic_list')
@router.post('/automatic_list')
def automatic_form():
	'''自動予約一覧画面を出力する
	- return : 自動予約一覧画面(HTML)
	'''
	# nav_menuのパラメータを整える
	page_title = config.__soft_name__ + " 自動予約一覧"
	btn_menu = ["","","","","","cliked",""]

	conn = mydb.connect(**config.database)
	cur = conn.cursor(dictionary=True)
	# 自動予約一覧データ
	sql = ( "SELECT * , `automatic`.`ID` AS automatic_id , `automatic`.`タイプ` AS automatic_type , `automatic`.`更新日時` AS update_at "
			"FROM `automatic` "
			"LEFT JOIN `channels` ON (`automatic`.`サービスID`   = `channels`.`サービスID`) "
			"LEFT JOIN `genres`   ON (`automatic`.`ジャンル番号` = `genres`.`ジャンル番号`) "
			"ORDER BY `優先順位` , `automatic`.`更新日時` ASC ")
	cur.execute(sql)
	rows = cur.fetchall()

	# 自動予約データの一部を表示のために変える
	for row in rows:
		# 自動予約に関連付けられている有効予約件数
		sql = "SELECT COUNT(*) AS CNT FROM `programs` WHERE (`自動予約ID` = %s ) AND (`予約` = '○') AND (`終了時刻` > NOW()) "
		cur.execute(sql , (row['automatic_id'],))
		cnt = cur.fetchone()
		row['予約件数'] = cnt['CNT']

		match row['automatic_type']:
			case 'NO':
				row['automatic_type'] = ''
			case 'GR':
				row['automatic_type'] = '地デジ'
			case 'BS':
				row['automatic_type'] = 'ＢＳ'
			case 'CS':
				row['automatic_type'] = 'ＣＳ'

		if row['サービス名'] is None:
			row['サービス名'] = ''

		if row['ジャンル'] is None:
			row['ジャンル'] = ''

		row['更新日'] = row['update_at'].strftime('%Y/%m/%d %H:%M')

	cur.close()
	conn.close()

	# テンプレートに入れる
	# <head> 作成
	add_js   = '<script src="/static/js/g05.js"></script>'
	add_css  = '<link rel="stylesheet" href="/static/css/g05.css">'
	template = env_j2.get_template('html91.j2')
	head = template.render(software=config.software , page_title=page_title , add_css=add_css , add_js=add_js)

	# <header>作成
	template = env_j2.get_template('html92.j2')
	header = template.render(page_title=page_title , btn_menu=btn_menu )

	# <main>作成
	template = env_j2.get_template('html05.j2')
	main = template.render(automatic_list=rows)

	# <footer>作成
	template = env_j2.get_template('html93.j2')
	footer = template.render(footer_str=config.footer_str)

	# データを返す
	return HTMLResponse(content=head + header + main + footer)
# --------------------------------------------------
@router.post('/set_keyword')
def set_keyword(keyword_data:dict):
	'''自動予約設定を登録する。データはすべて文字列で来ることに注意
	- keyword_data['key_word'] : キーワード
	- keyword_data['service_type'] : サービスタイプ NOの場合は指定なし
	- keyword_data['service_id'] : サービスID 0の場合は指定なし
	- keyword_data['genre'] : ジャンル番号 99の場合は指定なし
	- keyword_data['priority'] : 優先順位
	- keyword_data['margin_before'] : 録画マージン前
	- keyword_data['margin_after'] : 録画マージン後
	- return : 実行結果
	'''
	conn = mydb.connect(**config.database)
	cur = conn.cursor(dictionary=True)

	# automatic テーブル登録
	param = [ keyword_data['key_word'] , keyword_data['service_type'] , keyword_data['service_id'] , keyword_data['genre'] ,
			  keyword_data['margin_before'] , keyword_data['margin_after'] , keyword_data['priority'] ]

	sql = ("INSERT INTO `automatic` (`キーワード` , `タイプ` , `サービスID` , `ジャンル番号` , "
		   "`録画マージン前` , `録画マージン後` , `優先順位`) "
		   "VALUE (%s , %s , %s , %s , %s , %s , %s)")
	cur.execute(sql, param)
	automatic_id = cur.lastrowid	# 挿入されたデータのID conn.insert_id()でも可

	cur.close()
	conn.close()

	# 自動予約を編集したらすべての予約を再編成する
	result = g94.rebuild_reserved()	# 番組予約再構築
	result['自動予約ID'] = automatic_id
	return result
# --------------------------------------------------
@router.get('/load_keyword/{automatic_id}')
def load_keyword(automatic_id:int):
	'''自動予約設定の情報を返す
	- automatic_id : 自動予約ID
	- return : 自動予約設定の内容(HTML)
	'''
	conn = mydb.connect(**config.database)
	cur = conn.cursor(dictionary=True)

	cur.execute("SELECT * FROM `automatic` WHERE `ID` = %s ",(automatic_id,))
	automatic = cur.fetchone()

	cur.close()
	conn.close()

	service_type_selected = g91.make_service_type_selected(automatic['タイプ'])
	service_id_selected   = g91.get_option_service_id_selected(automatic['タイプ'] , automatic['サービスID'])
	option_genre          = g91.make_genre_option(automatic['ジャンル番号'])

	template = env_j2.get_template('html15.j2')
	keyword = template.render(automatic=automatic , service_type_selected=service_type_selected , service_id_selected=service_id_selected , option_genre=option_genre)
	return HTMLResponse(content=keyword)
# --------------------------------------------------
@router.post('/update_keyword')
def update_keyword(update_data:dict):
	'''自動予約設定を更新する
	- update_data['automatic_id'] : 自動予約ID
	- update_data['key_word'] : キーワード
	- update_data['service_type'] : サービスタイプ NOの場合は指定なし
	- update_data['service_id'] : サービスID 0の場合は指定なし
	- update_data['genre'] : ジャンル番号 99の場合は指定なし
	- update_data['priority'] : 優先順位
	- update_data['margin_before'] : 録画マージン前
	- update_data['margin_after'] : 録画マージン後
	- return : 実行結果
	'''
	conn = mydb.connect(**config.database)
	cur = conn.cursor(dictionary=True)

	# 自動予約情報更新
	sql = ("UPDATE `automatic` SET `タイプ` = %s , `サービスID` = %s , `ジャンル番号` = %s , "
		   "`録画マージン前` = %s , `録画マージン後` = %s , `優先順位` = %s "
		   "WHERE `ID` = %s ")
	param = [ update_data['service_type'] , update_data['service_id'] , update_data['genre'] ,
			 update_data['margin_before'] , update_data['margin_after'] , update_data['priority'] ,
			 update_data['automatic_id'] ]
	cur.execute(sql, param)

	cur.close()
	conn.close()

	# 自動予約を編集したらすべての予約を再編成する
	result = g94.rebuild_reserved()	# 番組予約再構築
	result['自動予約ID'] = update_data['automatic_id']
	return result
# --------------------------------------------------
@router.get('/delete_keyword/{automatic_id}')
def delete_keyword(automatic_id:int):
	'''自動予約設定を削除する
	- automatic_id : 自動予約ID
	- return : 実行結果
	'''
	conn = mydb.connect(**config.database)
	cur = conn.cursor(dictionary=True)

	# 自動予約情報削除
	cur.execute("DELETE FROM `automatic` WHERE `ID` = %s ",(automatic_id,))
	# 番組の予約情報クリア
	cur.execute("UPDATE `programs` SET `予約` = NULL , `自動予約ID` = NULL , `保存ファイル名` = NULL WHERE `自動予約ID` = %s ",(automatic_id,))

	cur.close()
	conn.close()

	# 自動予約を編集したらすべての予約を再編成する
	result = g94.rebuild_reserved()		# 番組予約再構築
	result['自動予約ID'] = automatic_id
	return result
# --------------------------------------------------
@router.get('/view_reserved/{automatic_id}')
def view_reserved(automatic_id:int):
	'''自動予約に関連付けられている番組を検索してデータを返す
	- automatic_id : 自動予約ID
	'''
	conn = mydb.connect(**config.database)
	cur = conn.cursor(dictionary=True)

	# 検索実行
	program_list = []
	sql = ("SELECT * "
			"FROM `programs` "
			"LEFT JOIN `channels`  ON (`programs`.`サービスID`   = `channels`.`サービスID`) "
			"LEFT JOIN `genres`    ON (`programs`.`ジャンル番号` = `genres`.`ジャンル番号`) "
			"WHERE (`自動予約ID` = %s) "
			"AND (`終了時刻` > NOW()) "
			"AND (`有効` = 'checked') "
			"ORDER BY `開始時刻` , `表示順` , `チャンネル` , `channels`.`サービスID` ")
	cur.execute(sql, (automatic_id,))
	programs = cur.fetchall()

	# 一覧表データ整形
	if cur.rowcount >= 1:
		for program in programs:
			data = {}
			data['放送日']         = program['開始時刻'].strftime('%m月%d日(%a)')
			data['予約状況']       = '-' if program['予約'] is None else program['予約']
			data['サービス名']     = program["サービス名"]
			data['時間']           = f'{program["開始時刻"].strftime("%H:%M")} - {program["終了時刻"].strftime("%H:%M")}'
			if data['予約状況']   != '○':
				data['rec_status'] = 'not_reserved'
			else:
				data['rec_status'] = ''
			data['番組名']         = program["番組名"]
			data['ジャンル']       = program['ジャンル']
			program_list.append(data)

	cur.close()
	conn.close()

	# dialogの中身作成
	template = env_j2.get_template('html25.j2')
	tbody = template.render(program_list=program_list)
	# データを返す
	return HTMLResponse(content=tbody)
# --------------------------------------------------
def set_automatic_id():
	'''automaticテーブルを元に、programsテーブルの自動予約IDを再構築する

	`programs`.`自動予約ID`をすべて NULL にして、`automatic`テーブルの情報を関連付ける
	- return : 実行結果

	自動予約でない予約は数に含まない
	'''
	conn = mydb.connect(**config.database)
	cur = conn.cursor(dictionary=True)

	cur.execute("UPDATE `programs` SET `自動予約ID` = NULL ")	# すべてのデータについて自動予約設定との関連を切る

	cur.execute("SELECT * FROM `automatic` ORDER BY `優先順位` DESC , `更新日時` DESC ")	# 自動予約設定を読み出す
	automatics = cur.fetchall()

	valid_count   = 0
	invalid_count = 0
	# 予約する sql
	sql_a = ("UPDATE `programs` "
			 "SET `予約` = '○' , `自動予約ID` = %s , "
			 "`録画マージン前` = %s , `録画マージン後` = %s , `保存ファイル名` = %s "
			 "WHERE `ID` = %s ")
	# 自動予約IDを変更する sql (`予約`に○か×が入っている場合、自動予約IDのみ更新する)
	sql_b = ("UPDATE `programs` "
			 "SET `自動予約ID` = %s , "
			 "`録画マージン前` = %s , `録画マージン後` = %s , `保存ファイル名` = %s "
			 "WHERE `ID` = %s ")

	# 優先順位の低い（優先順位の値が大きい）ものから処理する。優先順位の比較をしなくて良い
	for automatic in automatics:
		# 番組検索条件
		param = ['%'+automatic['キーワード']+'%']	# LIKE で検索する場合は単語の前後に % を付けておく
		if automatic['タイプ'] != 'NO':
			and_type = "AND (`channels`.`タイプ` = %s) "
			param.append(automatic['タイプ'])
		else:
			and_type =""
		if automatic['サービスID'] != 0:
			and_service_id = "AND (`programs`.`サービスID` = %s) "
			param.append(automatic['サービスID'])
		else:
			and_service_id =""
		if automatic['ジャンル番号'] != 99:
			and_genre ="AND (`programs`.`ジャンル番号` = %s) "
			param.append(automatic['ジャンル番号'])
		else:
			and_genre = ""

		# 自動予約設定に合う番組を検索する
		sql =(	"SELECT * , `programs`.`ID` AS pid "
				"FROM `programs` "
				"LEFT JOIN `channels`  ON (`programs`.`サービスID` = `channels`.`サービスID`) "
				"LEFT JOIN `automatic` ON (`programs`.`自動予約ID` = `automatic`.`ID`) "
				"WHERE (`番組名` LIKE %s) "
				"AND (`有効` = 'checked') "
				"AND (`開始時刻` > NOW()) "
				f"{and_type} "
				f"{and_service_id} "
				f"{and_genre}" )
		cur.execute(sql, param)
		programs = cur.fetchall()

		# 検索したすべての番組について、データベースの情報を更新する
		for program in programs:
			if program['保存ファイル名'] is None:
				program['保存ファイル名'] = g92.make_save_file_name(program , config.save_macro) # 保存ファイル名を作る

			param = [automatic['ID'] , automatic['録画マージン前'] , automatic['録画マージン後'] , program['保存ファイル名'] , program['pid']]

			if program['予約'] is None:
				cur.execute(sql_a, param)	# 予約する sqlを使う
				valid_count += 1
			else:
				cur.execute(sql_b, param)	# 自動予約IDを変更する sqlを使う。自動予約IDは上書きする
				if program['予約'] == '○':
					valid_count += 1
				else:
					invalid_count += 1

	cur.close()
	conn.close()

	return {"result":True , "修正総数":valid_count + invalid_count , "内有効予約":valid_count , "内無効予約":invalid_count}
#---------------------------------------------------------------------------
