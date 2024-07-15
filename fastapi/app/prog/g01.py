# -*- coding: utf-8 -*-

#---------------------------------------------------------------------------
# 「週間番組表」ルーチン
#---------------------------------------------------------------------------
from jinja2 import Environment, FileSystemLoader
from fastapi import APIRouter, Form , Header
from fastapi.responses import HTMLResponse
import mysql.connector as mydb
import datetime
from prog import g91 , config

env_j2 = Environment(loader=FileSystemLoader('./templates'))

router = APIRouter(tags=['週間番組表'])
# --------------------------------------------------
@router.get('/weekly/{genre_no}')		# パスパラメータでジャンルを指定する
@router.get('/weekly')					# パスパラメータがない場合。上下の順番を入れ替えてはいけない
@router.post('/weekly')
def get_programs_weekly(genre_no:int=None,service_type:str=Form(None), service_id:int=Form(None),genre:int=Form(None),nav_day:str=Form(None),nav_time:int=Form(None),cookie: str = Header(None)):
	'''週間番組表を出力する
	- genre_no : ジャンル番号 0..15。フォームパラメータ、クッキーより優先される
	- service_type : サービスのタイプ  (GR | BS | CS) ない場合はGR
	- service_id : サービスID=0の場合は指定なし
	- genre : ジャンル番号=99の場合は 0にする ジャンル指定は必須
	- nav_day  : 表示する日にち ない場合は今日
	- nav_time : 表示する時間帯 ない場合は現在の時間帯
	- cookie : クッキーの文字列 name:str=Cookie()で取得することもできるが、Cookie()は1つのクッキーしか得られない
	- return : 週間番組表(HTML)
	'''
	# パスパラメータでジャンルを指定する場合
	if genre_no is not None and genre_no >=0 and genre_no < 16:
		genre = genre_no
	# クエリーパラメータにデフォルトを設定にする
	service_type , service_id , genre , nav_day , nav_time , start_time , end_time = g91.set_default_query_param(service_type , service_id , genre , nav_day , nav_time , cookie)
	if genre == 99:	# ジャンル番号=99の場合は 0 (ニュース／報道)にする ジャンル指定は必須
		genre = 0

	# nav_menuのパラメータを整える
	page_title = config.__soft_name__ + " 週間番組表"
	btn_menu = ["","cliked","","","","",""]		# ナビメニューのボタンに色をつける
	service_type_check = g91.make_service_type_checked(service_type)
	option_service_id , service_id_list , service_list = g91.make_nav_menu_service(service_type , service_id)
	option_genre = g91.make_genre_option(genre)
	nav_days_btn , nav_times_btn = g91.make_nav_menu_days(start_time)

	# ７日間、６時間、ジャンルで絞って、日付・時刻順に、データベースから番組情報を得る
	days_strs_j = []
	program_package_list = []
	conn = mydb.connect(**config.database)
	cur = conn.cursor(dictionary=True)
	for i in range(7):		# 7日間
		day_time = start_time + datetime.timedelta(days=i)
		days_strs_j.append(day_time.strftime('%m月%d日(%a)'))
		for j in range(6):	# 6時間
			time_b = day_time + datetime.timedelta(hours=j)
			time_e = day_time + datetime.timedelta(hours=(j+1))
			param = [time_b , time_e , service_type , genre]
			if service_id == 0:	# サービスの絞りなし
				and_service = ""
			else:
				and_service = "AND (`programs`.`サービスID` = %s) "
				param.append(service_id)

			sql = ("SELECT * , `programs`.`ID` AS ProgID "
					"FROM `programs` "
					"LEFT JOIN `channels` ON (`programs`.`サービスID`   = `channels`.`サービスID`) "
					"LEFT JOIN `genres`   ON (`programs`.`ジャンル番号` = `genres`.`ジャンル番号`) "
					"WHERE ((`開始時刻` >= %s) AND (`開始時刻` <  %s)) "
					"AND (`有効` = 'checked') "
					"AND (`タイプ` = %s) "
					"AND (`programs`.`ジャンル番号` = %s) "
					f"{and_service} "
					"ORDER BY `開始時刻` , `表示順` , `チャンネル` , `channels`.`サービスID` ")
			cur.execute(sql, param)
			programs = cur.fetchall()

			# html01.j2 に出力する番組情報を整える
			'''
			<div style="grid-row: 1 ; grid-column: 2;">
				<div id="40014108334" class="one_program genre0 ">
					ＢＳ日テレ<br>
					19:00 - 20:54<br>
					深層ＮＥＷＳ▽今一番知りたいニュースをどこよりも早く、どこよりも深くお届けします
				</div>
				<div id="40018129608" class="one_program genre0 ">
					ＢＳフジ・１８１<br>
					19:00 - 20:00<br>
					🈢プライムオンラインＴＯＤＡＹ
				</div>
			</div>
			'''
			if cur.rowcount >= 1:
				package = {}
				package['grid_row']    = j + 1
				package['grid_column'] = i + 2
				package['program_list'] = []

				for program in programs:
					genre_class = program["ジャンルクラス"]
					match program["予約"]:
						case '○':
							genre_class = genre_class + " valid_reserved"
						case '×':
							genre_class = genre_class + " invalid_reserved"
					if program['録画状況'] == '録画中':
							genre_class = genre_class + " on_recording"

					data = {}
					data['ID']          = program["ProgID"]
					data['genre_class'] = genre_class
					data['サービス名']  = program["サービス名"]
					data['時間']        = f'{program["開始時刻"].hour:02}:{program["開始時刻"].minute:02} - {program["終了時刻"].hour:02}:{program["終了時刻"].minute:02}'
					data['番組名']      = program["番組名"]
					if program["終了時刻"] < datetime.datetime.now():
						data['past_program'] = 'past_program'	# 過去番組クラス　半透明にする
					else:
						data['past_program'] = ''
					package['program_list'].append(data)

				program_package_list.append(package)

	cur.close()
	conn.close()

	# テンプレートに入れる
	# <head> 作成
	add_css = '<link rel="stylesheet" href="/static/css/g01.css">'
	template = env_j2.get_template('html91.j2')
	head = template.render(software=config.software , page_title=page_title , add_css=add_css)

	# <header>作成
	template = env_j2.get_template('html92.j2')
	header = template.render(page_title=page_title ,
							 btn_menu=btn_menu ,
							 service_flag=True ,
							 service_type_check=service_type_check , option_service_id=option_service_id , option_genre=option_genre ,
							 nav_days_btn=nav_days_btn , nav_times_btn=nav_times_btn , days_strs_j=days_strs_j )

	# <main>作成
	template = env_j2.get_template('html01.j2')
	main = template.render(start_time_hour=start_time.hour , program_package_list=program_package_list)

	# <footer>作成
	template = env_j2.get_template('html93.j2')
	footer = template.render(footer_str=config.footer_str)

	# データを返す
	response = HTMLResponse(content=head + header + main + footer)
	response.set_cookie(key='service_type', value=service_type , httponly=True)	# クッキーの設定
	response.set_cookie(key='service_id', value=service_id , httponly=True)
	response.set_cookie(key='genre', value=genre , httponly=True)
	response.set_cookie(key='nav_day', value=nav_day , httponly=True)
	response.set_cookie(key='nav_time', value=nav_time , httponly=True)
	return response
# --------------------------------------------------
