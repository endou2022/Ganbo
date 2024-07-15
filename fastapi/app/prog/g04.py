# -*- coding: utf-8 -*-

#---------------------------------------------------------------------------
# 「番組検索」ルーチン
#---------------------------------------------------------------------------
from jinja2 import Environment, FileSystemLoader
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import mysql.connector as mydb
from prog import g92 , config

env_j2 = Environment(loader=FileSystemLoader('./templates'))

router = APIRouter(tags=['番組検索'])
# --------------------------------------------------
@router.get('/program_search')
@router.post('/program_search')
def program_search():
	'''番組検索画面を出力する
	- return : 番組検索画面(HTML)
	'''
	# nav_menuのパラメータを整える
	page_title = config.__soft_name__ + " 番組検索"
	btn_menu = ["","","","","cliked","",""]		# ナビメニューのボタンに色をつける

	# 上段のフォームのパラメータ
	conn = mydb.connect(**config.database)
	cur = conn.cursor(dictionary=True)
	cur.execute("SELECT * FROM `setting` ")
	rows = cur.fetchall()
	default_set = {}
	for row in rows:
		default_set[row['キー']] = row['値']
	cur.close()
	conn.close()

	# テンプレートに入れる
	# <head> 作成
	add_js  = '<script src="/static/js/g04.js"></script>'
	add_css = '<link rel="stylesheet" href="/static/css/g02.css">'
	template = env_j2.get_template('html91.j2')
	head = template.render(software=config.software , page_title=page_title , add_css=add_css , add_js=add_js)

	# <header>作成
	template = env_j2.get_template('html92.j2')
	header = template.render(page_title=page_title , btn_menu=btn_menu)

	# <main>作成
	template = env_j2.get_template('html04.j2')
	main = template.render(search_param=default_set)

	# <footer>作成
	template = env_j2.get_template('html93.j2')
	footer = template.render(footer_str=config.footer_str)

	# データを返す
	return HTMLResponse(content=head + header + main + footer)
# --------------------------------------------------
@router.post('/search_prog')
def search_prog(search_data:dict):
	'''番組を検索してデータを返す
	- search_data : 検索条件、search_data はすべて文字列で来る
	- return : 検索結果(HTML)
	- link https://qiita.com/aKuad/items/e4d89b24a717c955d701 (2024/01/23)
	'''
	# 検索実行
	key_word = f"`番組名` LIKE '%{search_data['key_word']}%'"
	program_list = g92.search_programs(key_word , search_data)

	# <tbody>作成
	template = env_j2.get_template('html14.j2')
	tbody = template.render(program_list=program_list)
	# データを返す
	return HTMLResponse(content=tbody)
# --------------------------------------------------
