# ---------------------------------------------------------------------------
# 「設定」ルーチン
# ---------------------------------------------------------------------------
import json
import requests
import logging

from jinja2 import Environment, FileSystemLoader
from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse
import mysql.connector as mydb

from prog import g95, config

env_j2 = Environment(loader=FileSystemLoader('./templates'), autoescape=True)

router = APIRouter(tags=['設定'])
# --------------------------------------------------


@router.get('/set-ganbo')
@router.post('/set-ganbo')
def set_ganbo():
    '''設定画面を出力する
    - return : 設定画面(HTML)
    '''
    # nav_menuのパラメータを整える
    page_title = config.__soft_name__ + " 設定"
    btn_menu = ["", "", "", "", "", "", "cliked"]        # ナビメニューのボタンに色をつける

    # <head> 作成
    add_js = '<script src="/static/js/g07.js"></script>'
    add_css = '<link rel="stylesheet" href="/static/css/g07.css">'
    template = env_j2.get_template('html91.j2')
    head = template.render(software=config.software, page_title=page_title, add_js=add_js, add_css=add_css)

    # <header>作成
    template = env_j2.get_template('html92.j2')
    header = template.render(page_title=page_title, btn_menu=btn_menu)

    # <main>作成
    genres = get_color_from_db()                # データベースからジャンル別背景色を得る
    gr_services = get_services_from_db('GR')    # データベースからサービスを得る
    bs_services = get_services_from_db('BS')
    cs_services = get_services_from_db('CS')
    std_data = get_std_from_db()                # データベースから標準設定を得る
    template = env_j2.get_template('html07.j2')
    main = template.render(genres=genres,
                           gr_services=gr_services,
                           bs_services=bs_services,
                           cs_services=cs_services,
                           std_data=std_data)

    # <footer>作成
    template = env_j2.get_template('html93.j2')
    footer = template.render(footer_str=config.footer_str)

    return HTMLResponse(content=head + header + main + footer)
# --------------------------------------------------


def get_color_from_db():
    '''データベースからジャンル別背景色を得る
    - return : ジャンルデータ
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM `genres` ORDER BY `ジャンル番号`")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows
# --------------------------------------------------


def get_services_from_db(p_type: str):
    '''データベースからサービスを得る
    - p_type : サービスのタイプ (GR | BS | CS)
    - return : サービス情報
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)
    sql = ("SELECT `有効`,`表示順`,`チャンネル`,`サービスID`,`サービス名` "
           "FROM channels "
           "WHERE `タイプ`=%s "
           "ORDER BY `有効` DESC , `表示順` , `チャンネル` , `サービス名` ,`サービスID` ")
    cur.execute(sql, (p_type,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows
# --------------------------------------------------


def get_std_from_db():
    '''データベースから標準設定を得て、グローバル変数に登録する
    - return : 標準設定の値
    '''
    ret_data = {}
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM `setting` ')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    for row in rows:
        ret_data[row['キー']] = row['値']

    # グローバル変数への登録
    config.save_root = ret_data['保存ルート']                # 保存ルートディレクトリ。以下スタートアップ時にデータベースの値で書き換える
    config.save_macro = ret_data['保存ファイル名マクロ']     # 保存ファイル名(マクロ)
    config.mirakurun_ip = ret_data['IPアドレス']             # mirakurun IP アドレス
    config.mirakurun_port = ret_data['ポート番号']           # mirakurun ポート番号
    config.margin_before = ret_data['録画マージン前']        # 録画マージン前
    config.margin_after = ret_data['録画マージン後']         # 録画マージン後

    return ret_data
# --------------------------------------------------


@router.get('/test_addr_port/{ip_addr}/{port}')
def test_addr_port(ip_addr: str, port: int):
    '''mirakurunのバージョンとチューナー情報を得る
    - ip_addr : IPアドレス
    - port :  ポート番号
    - return : {"result":True|False , "html":成功した場合の内容 , "exception":失敗した場合の例外情報}
    - link https://shanai-se.blog/python/library-requests-error/ (2024/01/06)
    - link https://zenn.dev/fujimotoshinji/scraps/eab79293a0acaf (2024/01/06)
    '''
    url_version = f"http://{ip_addr}:{port}/api/version"
    url_tuners = f"http://{ip_addr}:{port}/api/tuners"
    try:
        response = requests.get(url_version, timeout=3)
        response.raise_for_status()
        version_json = json.loads(response.text)
        response = requests.get(url_tuners, timeout=3)
        response.raise_for_status()
        tuners = json.loads(response.text)

        template = env_j2.get_template('html17.j2')
        answer = template.render(m_ver=version_json['current'], tuners=tuners)
        return HTMLResponse(answer)
    except Exception as exp:
        logging.error(f'チューナー情報取得例外 {str(exp)}')
        answer = '<div class="msgbox error">チューナーの情報を取得できませんでした</div>'
        return HTMLResponse(answer)
# --------------------------------------------------


@router.post('/set_addr_port/{ip_addr}/{port}')
def set_addr_port(ip_addr: str, port: int):
    '''データベースへmirakurunのIPアドレスとポート番号を設定する
    - ip_addr : IPアドレス
    - port : ポート番号
    - return : 設定した結果
    '''
    try:
        conn = mydb.connect(**config.database)
        cur = conn.cursor(dictionary=True)
        cur.execute("UPDATE `setting` SET `値` = %s WHERE `キー` = %s ", (ip_addr, "IPアドレス"))
        cur.execute("UPDATE `setting` SET `値` = %s WHERE `キー` = %s", (port, "ポート番号"))
        cur.close()
        conn.close()

        # グローバル変数への登録
        config.mirakurun_ip = ip_addr
        config.mirakurun_port = port

        # チャンネルデータを更新する
        get_channels()
        answer = ('<div class="msgbox message"><form action="/set-ganbo" method="get">IPアドレスとポート番号を設定しました<br>\n'
                  'ページを再読み込みしてください&nbsp;<input type="submit" value="再読み込み"></form></div>\n')
        return HTMLResponse(answer)
    except Exception as exp:
        cur.close()
        conn.close()
        logging.error(f'IPアドレスとポート番号の設定で例外 {str(exp)}')
        answer = '<div class="msgbox error">エラーが起きたため、IPアドレスとポート番号の設定ができませんでした</div>'
        return HTMLResponse(answer)
# --------------------------------------------------


@router.post('/set_color')
def set_color(colors: list = Form()):
    '''データベースへジャンル別背景色を設定する

    list = Form()で同じ名前のアイテムをリスト化する。かなりの時間悩んだ
    - colors : フォームのデータ
    - return : 設定した結果
    '''
    try:
        conn = mydb.connect(**config.database)
        cur = conn.cursor(dictionary=True)
        # 色のデータをデータベースへ格納
        for i, color in enumerate(colors):                              # executemanyがうまく使えなかった
            sql = "UPDATE `genres` SET `色` = %s WHERE `ジャンル番号` = %s "
            cur.execute(sql, (color, i))

        # g93.css作成
        cur.execute("SELECT * FROM `genres` ORDER BY `ジャンル番号` ")  # ジャンルクラス名をデータベースから呼び出す
        rows = cur.fetchall()
        with open('static/css/g93.css', mode="w") as css_file:          # withブロックでは自動的に閉じてくれる
            css_file.write("/*\nジャンル別色設定ファイル\n*/\n")
            for row in rows:
                css_file.write(f".{row['ジャンルクラス']} {{background-color: {row['色']};}}\n")

        cur.close()
        conn.close()
        answer = '<div class="msgbox message">番組表の背景色を設定しました</div>'
        return HTMLResponse(answer)
    except Exception as exp:
        cur.close()
        conn.close()
        logging.error(f'番組表の背景色の設定で例外 {str(exp)}')
        answer = '<div class="msgbox error">エラーが起きたため、番組表の背景色の設定ができませんでした</div>'
        return HTMLResponse(answer)
# --------------------------------------------------


@router.post('/set_service')
def set_service(valid_list: list = Form(None), sort_list: list = Form(), service_id_list: list = Form(), service_type: str = Form()):
    '''サービスの有効、表示順を設定する
    - list valid_list : チェックされたチェックボックスのデータ 数は変動する
    - list sort_list : 表示順 サービスIDと同じ順で同じ数だけ
    - list service_id_list : サービスID
    - str service_type : サービスタイプ (GR | BS | CS)
    - return : 設定した結果
    '''
    try:
        conn = mydb.connect(**config.database)
        cur = conn.cursor(dictionary=True)

        # 「有効」のチェックボックスを反映させる
        cur.execute("UPDATE `channels` SET `有効` = '' WHERE `タイプ` = %s", (service_type,))                          # すべてを無効にして
        if valid_list is not None:
            for chk_service in valid_list:
                cur.execute("UPDATE `channels` SET `有効` = 'checked' WHERE `サービスID` = %s", (chk_service,))        # チェックのある物だけ有効にする

        # 「表示順」を反映させる
        for i, num in enumerate(sort_list):
            cur.execute("UPDATE `channels` SET `表示順` = %s WHERE `サービスID` = %s", (num, service_id_list[i]))      # チェックのある物だけ有効にする

        cur.close()
        conn.close()

        # 設定したデータを読み出す
        services = get_services_from_db(service_type)
        template = env_j2.get_template('html07-32.j2')
        answer = template.render(services=services)
        return HTMLResponse(answer)
    except Exception as exp:
        cur.close()
        conn.close()
        logging.error(f'サービスの設定で例外 {str(exp)}')
        answer = '<tr class="msgbox error"><td colspan="5">エラーが起きたため、サービスの設定ができませんでした</td></tr>'
        return HTMLResponse(answer)
# --------------------------------------------------


@router.post('/set_std')
def set_std(reflesh_time: str = Form(), margin_before: int = Form(), margin_after: int = Form(), save_file_root: str = Form(), save_file_macro: str = Form()):
    '''データベースへ録画標準設定を設定する
    - reflesh_time : 番組情報更新時刻
    - margin_before : 録画マージン前
    - margin_after : 録画マージン後
    - save_file_root : 保存ルート。compose.yml で指定するために編集不可
    - save_file_macro : 保存ファイル名マクロ
    - return : 設定した結果
    '''
    try:
        conn = mydb.connect(**config.database)
        cur = conn.cursor(dictionary=True)
        cur.execute("UPDATE `setting` SET `値` = %s WHERE `キー`='番組情報更新時刻' ", (reflesh_time, ))
        cur.execute("UPDATE `setting` SET `値` = %s WHERE `キー`='録画マージン前' ", (margin_before, ))
        cur.execute("UPDATE `setting` SET `値` = %s WHERE `キー`='録画マージン後' ", (margin_after, ))
        cur.execute("UPDATE `setting` SET `値` = %s WHERE `キー`='保存ルート' ", (save_file_root, ))
        cur.execute("UPDATE `setting` SET `値` = %s WHERE `キー`='保存ファイル名マクロ' ", (save_file_macro, ))
        cur.execute("ALTER TABLE `programs`  ALTER COLUMN `録画マージン前` SET DEFAULT %s ", (margin_before,))
        cur.execute("ALTER TABLE `programs`  ALTER COLUMN `録画マージン後` SET DEFAULT %s ", (margin_after,))
        cur.execute("ALTER TABLE `automatic` ALTER COLUMN `録画マージン前` SET DEFAULT %s ", (margin_before,))
        cur.execute("ALTER TABLE `automatic` ALTER COLUMN `録画マージン後` SET DEFAULT %s ", (margin_after,))
        cur.close()
        conn.close()

        # グローバル変数への登録
        config.save_root = save_file_root      # 保存ルートディレクトリ。以下スタートアップ時にデータベースの値で書き換える
        config.save_macro = save_file_macro    # 保存ファイル名(マクロ)
        config.margin_before = margin_before   # 録画マージン前
        config.margin_after = margin_after     # 録画マージン後

        g95.set_schedule(reflesh_time)         # 番組情報更新時刻を変更する
        answer = '<div class="msgbox message">標準設定を更新しました</div>'
        return HTMLResponse(answer)
    except Exception as exp:
        cur.close()
        conn.close()
        logging.error(f'標準設定で例外 {str(exp)}')
        answer = '<div class="msgbox error">エラーが起きたため、標準設定の更新ができませんでした</div>'
        return HTMLResponse(answer)
# --------------------------------------------------


def get_channels():
    '''サービス情報（チャンネル）を得て、データベースに格納する
    - return : {"result":True|False , "channels":サービスの数 , "exception":例外の内容}
    '''
    # mirakurunからチャンネルの情報をもらう
    url = f"http://{config.mirakurun_ip}:{config.mirakurun_port}/api/channels"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except Exception as exp:
        logging.error(f'サービス情報取得例外 {str(exp)}')
        return {"result": False, "exception": str(exp)}

    channels = json.loads(response.text)
    insert_data = []
    for channel in channels:
        channel_type = channel['type']
        channel_channel = channel['channel']
        services = channel['services']
        for service in services:
            sservice_id = service['id']
            service_service_id = service['serviceId']
            service_network_id = service['networkId']
            service_name = service['name']
            insert_data.append((channel_type, channel_channel, sservice_id, service_service_id, service_network_id, service_name))

    # データベースに格納
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)
    cur.execute("TRUNCATE TABLE `channels` ")    # テーブルを空にしてしまう
    sql = ("INSERT INTO `channels` "
           "(`タイプ` , `チャンネル` , `ID` , `サービスID` , `ネットワークID` , `サービス名`) VALUES "
           "(%s , %s , %s , %s , %s , %s) ")
    cur.executemany(sql, insert_data)

    cur.close()
    conn.close()
    return {"result": True, "channels": len(insert_data)}
# --------------------------------------------------
