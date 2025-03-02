# ---------------------------------------------------------------------------
# 「自動予約一覧」ルーチン
# ---------------------------------------------------------------------------
from jinja2 import Environment, FileSystemLoader
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import mysql.connector as mydb

from prog import g91, g92, g94, config

env_j2 = Environment(loader=FileSystemLoader('./templates'), autoescape=True)

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
    btn_menu = ["", "", "", "", "", "cliked", ""]

    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)
    # 自動予約一覧データ
    sql = ("SELECT * , `automatic`.`ID` AS automatic_id , `automatic`.`タイプ` AS automatic_type , `automatic`.`更新日時` AS update_at "
           "FROM `automatic` "
           "LEFT JOIN `channels` ON (`automatic`.`サービスID`   = `channels`.`サービスID`) "
           "LEFT JOIN `genres`   ON (`automatic`.`ジャンル番号` = `genres`.`ジャンル番号`) "
           "ORDER BY `automatic`.`更新日時` ASC ")
    cur.execute(sql)
    rows = cur.fetchall()

    # 自動予約データの一部を表示のために変える
    for row in rows:
        # 自動予約に関連付けられている有効予約件数
        sql = "SELECT COUNT(*) AS CNT FROM `programs` WHERE (`自動予約ID` = %s ) AND (`予約` = '○') AND (`終了時刻` > NOW()) "
        cur.execute(sql, (row['automatic_id'],))
        cnt = cur.fetchone()
        row['予約件数'] = cnt['CNT']
        # 自動予約に関連付けられている予約総数
        sql = "SELECT COUNT(*) AS CNT FROM `programs` WHERE (`自動予約ID` = %s ) AND (`終了時刻` > NOW()) "
        cur.execute(sql, (row['automatic_id'],))
        cnt = cur.fetchone()
        row['予約総数'] = cnt['CNT']

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
    add_js = '<script src="/static/js/g05.js"></script>'
    add_css = '<link rel="stylesheet" href="/static/css/g05.css">'
    template = env_j2.get_template('html91.j2')
    head = template.render(software=config.software, page_title=page_title, add_css=add_css, add_js=add_js)

    # <header>作成
    template = env_j2.get_template('html92.j2')
    header = template.render(page_title=page_title, btn_menu=btn_menu)

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
def set_keyword(keyword_data: dict):
    '''自動予約登録　データはすべて文字列で来ることに注意
    - keyword_data['key_word'] : キーワード
    - keyword_data['service_type'] : サービスタイプ NOの場合は指定なし
    - keyword_data['service_id'] : サービスID 0の場合は指定なし
    - keyword_data['genre'] : ジャンル番号 99の場合は指定なし
    - keyword_data['margin_before'] : 録画マージン前
    - keyword_data['margin_after'] : 録画マージン後
    - return : {'自動予約ID(登録)' , '予約番組数'}
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    # automatic テーブル登録
    param = [keyword_data['key_word'], keyword_data['service_type'], keyword_data['service_id'], keyword_data['genre'], keyword_data['margin_before'], keyword_data['margin_after']]
    sql = ("INSERT INTO `automatic` (`キーワード` , `タイプ` , `サービスID` , `ジャンル番号` , ""`録画マージン前` , `録画マージン後`) "
           "VALUE (%s , %s , %s , %s , %s , %s )")
    cur.execute(sql, param)
    automatic_id = cur.lastrowid                # 挿入されたデータのID conn.insert_id()でも可

    cur.close()
    conn.close()

    num = search_reserve_and_set(automatic_id)  # 番組予約、タスク作成
    result = {}
    result['自動予約ID(登録)'] = automatic_id
    result['予約番組数'] = num
    return result
# --------------------------------------------------


@router.get('/load_keyword/{automatic_id}')
def load_keyword(automatic_id: int):
    '''自動予約設定の情報を返す
    - automatic_id : 自動予約ID
    - return : 自動予約設定の内容(HTML)
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM `automatic` WHERE `ID` = %s ", (automatic_id,))
    automatic = cur.fetchone()

    cur.close()
    conn.close()

    service_type_selected = g91.make_service_type_selected(automatic['タイプ'])
    service_id_selected = g91.get_option_service_id_selected(automatic['タイプ'], automatic['サービスID'])
    option_genre = g91.make_genre_option(automatic['ジャンル番号'])

    template = env_j2.get_template('html15.j2')
    keyword = template.render(automatic=automatic, service_type_selected=service_type_selected,
                              service_id_selected=service_id_selected, option_genre=option_genre)
    return HTMLResponse(content=keyword)
# --------------------------------------------------


@router.post('/update_keyword')
def update_keyword(update_data: dict):
    '''自動予約設定を更新する
    - update_data['automatic_id'] : 自動予約ID
    - update_data['key_word'] : キーワード
    - update_data['service_type'] : サービスタイプ NOの場合は指定なし
    - update_data['service_id'] : サービスID 0の場合は指定なし
    - update_data['genre'] : ジャンル番号 99の場合は指定なし
    - update_data['margin_before'] : 録画マージン前
    - update_data['margin_after'] : 録画マージン後
    - return : {自動予約ID(削除)','削除した番組数','自動予約ID(登録)' , '予約番組数'}
    '''
    result_d = delete_keyword(update_data['automatic_id'])
    result_s = set_keyword(update_data)

    return result_d | result_s
# --------------------------------------------------


@router.get('/delete_keyword/{automatic_id}')
def delete_keyword(automatic_id: int):
    '''自動予約設定を削除する
    - automatic_id : 自動予約ID
    - return : {'自動予約ID(削除)','削除した番組数'}
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    # 自動予約情報削除
    cur.execute("DELETE FROM `automatic` WHERE `ID` = %s ", (automatic_id,))

    # 自動予約に関連付けられている予約を解除しタスクを削除
    cur.execute("SELECT * FROM `programs` WHERE `自動予約ID` = %s ", (automatic_id,))
    programs = cur.fetchall()
    for program in programs:
        cur.execute("UPDATE `programs` SET `予約` = NULL , `自動予約ID` = NULL , `保存ファイル名` = NULL WHERE `ID` = %s ", (program['ID'],))
        g94.del_rec_task(program['ID'])

    cur.close()
    conn.close()

    result = {}
    result['自動予約ID(削除)'] = automatic_id
    result['削除した番組数'] = len(programs)
    return result
# --------------------------------------------------


@router.get('/view_reserved/{automatic_id}')
def view_reserved(automatic_id: int):
    '''自動予約に関連付けられている番組を検索してデータを返す
    - automatic_id : 自動予約ID
    - return 予約一覧表(HTML)
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
            data['放送日'] = program['開始時刻'].strftime('%m月%d日(%a)')
            data['予約状況'] = '-' if program['予約'] is None else program['予約']
            data['サービス名'] = program["サービス名"]
            data['時間'] = f'{program["開始時刻"].strftime("%H:%M")} - {program["終了時刻"].strftime("%H:%M")}'
            if data['予約状況'] != '○':
                data['rec_status'] = 'not_reserved'
            else:
                data['rec_status'] = ''
            data['番組名'] = program["番組名"]
            data['ジャンル'] = program['ジャンル']
            program_list.append(data)

    cur.close()
    conn.close()

    # dialogの中身作成
    template = env_j2.get_template('html25.j2')
    tbody = template.render(program_list=program_list)
    # データを返す
    return HTMLResponse(content=tbody)
# --------------------------------------------------


def search_reserve_and_set(automatic_id: int):
    '''自動予約番号に従い予約登録・タスク作成。
    「条件に合う AND 予約 is NULL AND 未来に開始」する番組を予約し、録画タスクを作る

    - int automatic_id: 自動予約番号
    - return 予約した番組数
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    sql = "SELECT * FROM `automatic` WHERE ID = %s "
    cur.execute(sql, (automatic_id,))
    automatic = cur.fetchone()

    # 条件設定
    param = []
    # https://stackoverflow.com/questions/24072084/like-in-mysql-connector-python (2025/01/16)
    param.append(f"%{automatic['キーワード']}%")    # LIKEを使う場合はsql文の外で % を付けておく

    if automatic['タイプ'] == 'NO':                 # サービスタイプの絞りなし
        and_type = ""
    else:
        and_type = "AND (`channels`.`タイプ` = %s) "
        param.append(automatic['タイプ'])

    if automatic['サービスID'] == 0:                # サービスの絞りなし
        and_service = ""
    else:
        and_service = "AND (`programs`.`サービスID` = %s) "
        param.append(automatic['サービスID'])

    if automatic['ジャンル番号'] == 99:             # ジャンルの絞りなし
        and_genre = ""
    else:
        and_genre = "AND (`programs`.`ジャンル番号` = %s) "
        param.append(automatic['ジャンル番号'])

    # 検索　条件に合う AND 予約されていない AND 未来に開始
    sql = ("SELECT * , `programs`.`ID` AS ProgID , `programs`.`サービスID` AS sid "
           "FROM `programs` "
           "LEFT JOIN `channels` ON (`programs`.`サービスID`   = `channels`.`サービスID`) "
           "LEFT JOIN `genres`   ON (`programs`.`ジャンル番号` = `genres`.`ジャンル番号`) "
           "WHERE (`開始時刻` > NOW()) AND (`予約` is NULL) AND (`番組名` LIKE %s) "
           f"{and_type} "
           f"{and_service} "
           f"{and_genre} ")
    cur.execute(sql, param)
    programs = cur.fetchall()

    # 予約する sql
    sql_a = ("UPDATE `programs` "
             "SET `予約` = '○' , `自動予約ID` = %s , `録画マージン前` = %s , `録画マージン後` = %s , `保存ファイル名` = %s "
             "WHERE `ID` = %s ")
    # 検索したすべての番組について
    for program in programs:
        if program['保存ファイル名'] is None:
            program['保存ファイル名'] = g92.make_save_file_name(program, config.save_macro)  # 保存ファイル名を作る

        # 予約設定する
        param = [automatic['ID'], automatic['録画マージン前'], automatic['録画マージン後'], program['保存ファイル名'],
                 program['ProgID']]
        cur.execute(sql_a, param)
        program['録画マージン前'] = automatic['録画マージン前']
        program['録画マージン後'] = automatic['録画マージン後']

        # 録画タスク登録
        g94.del_rec_task(program['ProgID'])     # すでに登録されている予約があれば削除して新しく予約タスクを作る
        g94.rec_task_create(program)            # 番組情報から録画タスクを作る

    cur.close()
    conn.close()

    return len(programs)
# ---------------------------------------------------------------------------
