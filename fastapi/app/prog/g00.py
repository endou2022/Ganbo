# ---------------------------------------------------------------------------
# 「番組表」ルーチン
# ---------------------------------------------------------------------------
import datetime

import mysql.connector as mydb
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from prog import config, g91

env_j2 = Environment(loader=FileSystemLoader('./templates'), autoescape=True)
router = APIRouter(tags=['番組表'])
# --------------------------------------------------


@router.get('/')
@router.get('/daily')
@router.post('/daily')
async def get_programs_daily(request: Request):
    '''番組表を出力する
    - request: Request フォームからのパラメータ
    - return : 番組表(HTML)
    - link https://www.nblog09.com/w/2019/01/05/python-decorator/ (2024/04/01)
    '''
    '''
    docstringについて、Swagger UI , ReDoc で見やすいような形式にした。
    https://self-methods.com/fastapiapi-tag-docstring/ (2024/05/01)
    markdown 形式と似た表記ができるらしい。
    '''
    '''
    Query , Form , Header などはデコレーターの直後でなければ使うことができない
    本来は @router.get() で受けるべきだが、パスパラメータを表示したくなかったので、FORM メソッドを post にし、 @router.post() とした。
    また、アドレス欄に直打ちして番組表を表示したかったので、デコレータを２重にした。
    '''
    cookies = request.cookies                   # cookiesは最初からdict # Qwen3-Max 2025/10/11
    form_data = dict(await request.form())      # Form()パラメータ

    # クエリーパラメータにデフォルトを設定にする
    service_type, service_id, genre, nav_day, nav_time, start_time, end_time = g91.set_default_query_param(cookies , form_data)

    # nav_menuのパラメータを整える
    page_title = config.__soft_name__ + " 番組表"
    btn_menu = ["cliked", "", "", "", "", "", ""]        # ナビメニューのボタンに色をつける
    service_type_check = g91.make_service_type_checked(service_type)
    option_service_id, service_id_list, service_list = g91.make_nav_menu_service(service_type, service_id)
    option_genre = g91.make_genre_option(genre)
    nav_days_btn, nav_times_btn = g91.make_nav_menu_days(start_time)

    # 表示するサービス軸データを整える
    # サービスの個数が変動するのでプログラムで作る
    tv_programs_style = f'<style>\n\t\t.tv-programs-header , .tv-programs {{grid-template-columns: 20px repeat({len(service_list)}, 150px);}}\n\t</style>'

    # サービスの数だけ、サービス順に、データベースから番組情報を得る
    program_list = []
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)
    for index, service_id2 in enumerate(service_id_list):
        param = [start_time, end_time, start_time, end_time, start_time, end_time, service_id2]
        if genre == 99:        # ジャンルの絞りなし
            and_genre = ""
        else:
            and_genre = "AND (`programs`.`ジャンル番号` = %s) "
            param.append(genre)
        sql = ("SELECT * , "
               "CASE WHEN `開始時刻` < %s THEN '表の前から' "
               "     WHEN `終了時刻` > %s THEN '表の後まで' "
               "     ELSE '表の中' "
               "END AS `番組表フラグ` "
               "FROM `programs` "
               "LEFT JOIN `genres` ON (`programs`.`ジャンル番号` = `genres`.`ジャンル番号`) "
               "WHERE (((`開始時刻` >= %s) AND (`開始時刻` <  %s)) OR "
               "((`終了時刻` >  %s) AND (`終了時刻` <= %s))) "
               "AND (`サービスID` = %s) "
               f"{and_genre} "
               "ORDER BY `開始時刻` ")
        cur.execute(sql, param)
        programs = cur.fetchall()

        # html00.j2 に出力する番組情報を整える
        '''
        grid-row = 1 +  (放送開始時刻(H) - 番組表先頭時刻(H)) * 60 / span [放送時間(m)]
        grid-column = 1 + i
        ex.
        <div id="123456" class="content-area" style="grid-row: 323 / span 6; grid-column: 2;">
            <div class="content-time">23:22 - 23:28</div>
            <div class="content-title">テレニュース🈑</div>
            <div class="content-discription">この時間帯で起きた最新ニュースを短い時間の中で</div>
        </div>
        '''
        for program in programs:
            data = {}
            genre_class = program["ジャンルクラス"]
            match program["予約"]:
                case '○':
                    genre_class = genre_class + " valid_reserved"
                case '×':
                    genre_class = genre_class + " invalid_reserved"
            if program['録画状況'] == '録画中':
                genre_class = genre_class + " on_recording"

            # program_start_time は datetime
            program_start_time = program['開始時刻']
            if program['番組表フラグ'] == '表の前から':
                data['grid_row'] = 1
                d = program["終了時刻"] - start_time  # d は timedelta
                data['span'] = int(d.total_seconds() / 60)
            if program['番組表フラグ'] == '表の後まで':
                data['grid_row'] = 1 + (program_start_time.hour - start_time.hour) * 60 + program_start_time.minute
                d = end_time - program["開始時刻"]
                data['span'] = int(d.total_seconds() / 60)
            if program['番組表フラグ'] == '表の中':
                data['grid_row'] = 1 + (program_start_time.hour - start_time.hour) * 60 + program_start_time.minute
                data['span'] = int(program['放送時間'] / 60)

            if program["終了時刻"] < datetime.datetime.now():
                data['past_program'] = 'past_program'    # 過去番組クラス　半透明にする
            else:
                data['past_program'] = ''

            data['ID'] = program["ID"]
            data['genre_class'] = genre_class
            data['grid_column'] = 2 + index
            data['時間'] = f'{program["開始時刻"].hour:02}:{program["開始時刻"].minute:02} - {program["終了時刻"].hour:02}:{program["終了時刻"].minute:02}'
            data['番組名'] = program["番組名"]
            data['説明'] = program["説明"]
            program_list.append(data)

    cur.close()
    conn.close()

    # テンプレートに入れる 引数が多くなったので、テンプレートをいくつかに分けた
    # <head> 作成
    add_css = '<link rel="stylesheet" href="/static/css/g00.css">'
    template = env_j2.get_template('html91.j2')
    head = template.render(software=config.software, page_title=page_title, tv_programs_style=tv_programs_style, add_css=add_css)

    # <header>作成
    template = env_j2.get_template('html92.j2')
    header = template.render(page_title=page_title,
                             btn_menu=btn_menu,
                             service_flag=True,
                             service_type_check=service_type_check, option_service_id=option_service_id, option_genre=option_genre,
                             nav_days_btn=nav_days_btn, nav_times_btn=nav_times_btn, service_list=service_list)

    # <main>作成
    template = env_j2.get_template('html00.j2')
    main = template.render(start_time_hour=start_time.hour, program_list=program_list)

    # <footer>作成
    template = env_j2.get_template('html93.j2')
    footer = template.render(footer_str=config.footer_str)

    # データを返す
    response = HTMLResponse(content=head + header + main + footer)
    # https://stackoverflow.com/questions/77008824/how-to-set-cookies-on-jinja2-templateresponse-in-fastapi (2024/01/20)
    # 返すデータでクッキーを設定しなければならない
    response.set_cookie(key='service_type', value=service_type, httponly=True)    # クッキーの設定
    response.set_cookie(key='service_id', value=service_id, httponly=True)
    response.set_cookie(key='genre', value=genre, httponly=True)
    response.set_cookie(key='nav_day', value=nav_day, httponly=True)
    response.set_cookie(key='nav_time', value=nav_time, httponly=True)
    # https://liquids.dev/articles/17778473-418a-4422-94c1-ee10fb024869 (2024/01/20)
    # クッキーの max_age を設定しないので、有効期限はブラウザを閉じるまで
    # JavaScript からの直接の参照・操作を禁止
    return response
# --------------------------------------------------
