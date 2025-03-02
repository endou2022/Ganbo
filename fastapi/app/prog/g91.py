# ---------------------------------------------------------------------------
# 共通ルーチン
# ---------------------------------------------------------------------------
import datetime

from jinja2 import Environment, FileSystemLoader
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import mysql.connector as mydb

from prog import g92, g94, config

env_j2 = Environment(loader=FileSystemLoader('./templates'), autoescape=True)

router = APIRouter(tags=['共通ルーチン1'])
# ---------------------------------------------------------------------------


def set_default_query_param(service_type: str, service_id: int, genre: int, nav_day: str, nav_time: int, cookie_str: str):
    '''クエリーパラメータにデフォルトを設定にする

    フォームからのパラメータがない場合、クッキーをデフォルトを設定にする
    - service_type : サービスのタイプ  (GR | BS | CS) ない場合はGR
    - service_id : サービスID=0の場合は指定なし
    - genre : ジャンル番号=99の場合は指定なし
    - nav_day  : 表示する日にち ない場合は今日
    - nav_time : 表示する時間帯 ない場合は現在の時間帯
    - cookie_str : クッキーの文字列
    - return : クエリーパラメータ
    '''
    # クッキーやHTMLからのフォーム変数を辞書として受け取る方法はないものか
    # クッキー文字列を分解してクッキーを得る --> 文字列なので適切な型に変換する必要がある。
    # pythonはインタプリタで実装されているので、適宜型を変換してくれるものと思っていた
    cookies = {}
    if cookie_str is not None:
        cookie_str_list = cookie_str.split(';')
        for key_val_str in cookie_str_list:
            key_val_list = key_val_str.split('=')
            cookies[str.strip(key_val_list[0])] = str.strip(key_val_list[1])

    # フォームからのパラメータがない場合、クッキーをデフォルトを設定にする
    if service_type is None:
        if 'service_type' in cookies:
            service_type = cookies['service_type']     # クッキー
        else:
            service_type = "GR"                        # デフォルト

    if service_id is None:
        if 'service_id' in cookies:
            service_id = int(cookies['service_id'])
        else:
            service_id = 0                             # 0は指定なし 番兵プログラムだ！(;_;)

    if genre is None:
        if 'genre' in cookies:
            genre = int(cookies['genre'])
        else:
            genre = 99                                 # 99は指定なし

    if nav_day is None:
        if 'nav_day' in cookies:
            nav_day = cookies['nav_day']
            dt_c = datetime.datetime.strptime(nav_day, '%Y-%m-%d')
            if dt_c < datetime.datetime.now():
                nav_day = datetime.datetime.now().strftime('%Y-%m-%d')
        else:
            nav_day = datetime.datetime.now().strftime('%Y-%m-%d')

    nav_time_flag = False
    if nav_time is None:
        if 'nav_time' in cookies:
            nav_time = int(cookies['nav_time'])
        else:
            nav_time = 6 * (datetime.datetime.now().hour // 6)  # '//' 整数除算(割り算の整数部)

    if nav_time == 24:
        nav_time = 0
        nav_time_flag = True

    # 番組表示開始時間
    start_time = datetime.datetime.strptime(f"{nav_day} {nav_time}:00:00", '%Y-%m-%d %H:%M:%S')
    if nav_time_flag:
        start_time = start_time + datetime.timedelta(days=1)    # 次の日
        dt = start_time - datetime.datetime.now()
        if dt.days == 7:
            start_time = start_time - datetime.timedelta(days=8)

    # 番組表示終了時間
    end_time = start_time + datetime.timedelta(hours=6)

    return service_type, service_id, genre, nav_day, nav_time, start_time, end_time
# ---------------------------------------------------------------------------


def make_nav_menu_days(start_time: datetime.datetime):
    '''nav_menuの日付ボタン、時間帯ボタンデータを作る
    - start_time : 番組表開始時刻
    - return : nav_days_btn 日付ボタン
    - return : nav_times_btn 時間帯ボタン
    '''
    btn_day = start_time.strftime('%Y-%m-%d')
    btn_hour = start_time.hour
    # 日付ボタンを作る
    today = datetime.datetime.now()
    nav_days_btn = []
    for i in range(8):
        radio_data = {}
        d = today + datetime.timedelta(days=i)
        dc = d.strftime('%Y-%m-%d')
        dj = d.strftime('%m月%d日(%a)')
        radio_data['Ymd'] = dc
        radio_data['ja'] = dj
        if btn_day == dc:
            radio_data['checked'] = 'checked'
        else:
            radio_data['checked'] = ''
        nav_days_btn.append(radio_data)

    # 時間帯ボタンを作る
    nav_time_list = [0, 6, 12, 18, 24]
    nav_times_btn = []
    for i in range(5):
        radio_data = {}
        radio_data['value'] = nav_time_list[i]
        radio_data['label'] = f'{nav_time_list[i]:02}'
        if btn_hour == nav_time_list[i]:
            radio_data['checked'] = 'checked'
        else:
            radio_data['checked'] = ''
        nav_times_btn.append(radio_data)

    return nav_days_btn, nav_times_btn
# ---------------------------------------------------------------------------


def make_nav_menu_service(nav_type: str, nav_service_id: int):
    '''nav_menuのサービスプルダウンを作る
    - nav_type : 放送タイプ (GR | BS | CS)
    - nav_service_id : サービスID
    - return : option_service_id サービスIDの<option>
    - return : service_id_list サービスIDのリスト
    - return : service_list サービス名のリスト
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    # サービス プルダウンメニューの<option>を作る
    sql = ("SELECT `サービスID`,`サービス名` "
           "FROM `channels` "
           "WHERE (`タイプ`=%s) AND (`有効` = 'checked') "
           "ORDER BY `表示順` , `チャンネル` , `サービスID` ")
    cur.execute(sql, (nav_type,))
    rows = cur.fetchall()
    rows.insert(0, {'サービスID': 0, 'サービス名': ''})  # <option>のため先頭に追加
    option_service_id = []
    for row in rows:
        option_data = {}
        option_data['サービスID'] = row['サービスID']
        option_data['サービス名'] = row['サービス名']
        if row['サービスID'] == nav_service_id:
            option_data['selected'] = 'selected'
        else:
            option_data['selected'] = ''
        option_service_id.append(option_data)

    # 表示するサービスのリストを作る
    service_id_list = []
    service_list = []
    if nav_service_id == 0:    # サービスを絞り込まない
        cur.execute("SELECT `サービスID`,`サービス名` FROM `channels` WHERE (`タイプ`=%s) AND (`有効` = 'checked') ORDER BY `表示順` , `チャンネル` , `サービスID` ", (nav_type,))
        rows = cur.fetchall()
        for row in rows:
            service_id_list.append(row['サービスID'])
            service_list.append(row['サービス名'])
    else:
        cur.execute("SELECT `サービスID`,`サービス名` FROM `channels` WHERE `サービスID`=%s ", (nav_service_id,))
        row = cur.fetchone()
        service_id_list.append(row['サービスID'])
        service_list.append(row['サービス名'])

    cur.close()
    conn.close()

    return option_service_id, service_id_list, service_list
# ---------------------------------------------------------------------------


def make_service_type_checked(nav_type: str):
    '''サービスタイプボタンニューの checked 属性データを作る
    - nav_type : 放送タイプ (GR | BS | CS)
    - return : service_type_check サービスタイプの checked 属性
    '''
    service_type_check = {"GR": "", "BS": "", "CS": ""}
    match nav_type:
        case 'GR':
            service_type_check['GR'] = 'checked'
        case 'BS':
            service_type_check['BS'] = 'checked'
        case 'CS':
            service_type_check['CS'] = 'checked'

    return service_type_check
# ---------------------------------------------------------------------------


def make_service_type_selected(nav_type: str = "NO"):
    '''サービスタイププルダウンニューの selected 属性データを作る
    - nav_type : 放送タイプ (NO | GR | BS | CS)
    - return : service_type_selected サービスタイプの selected 属性
    '''
    service_type_selected = {"NO": "", "GR": "", "BS": "", "CS": ""}
    match nav_type:
        case 'NO':
            service_type_selected['NO'] = 'selected'
        case 'GR':
            service_type_selected['GR'] = 'selected'
        case 'BS':
            service_type_selected['BS'] = 'selected'
        case 'CS':
            service_type_selected['CS'] = 'selected'

    return service_type_selected
# ---------------------------------------------------------------------------


def make_genre_option(nav_genre: int):
    '''ジャンルプルダウンメニューの<option>のデータを作る
    - nav_genre : ジャンル番号
    - return : option_genre ジャンルの<option>データ
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    # ジャンル プルダウンメニューの<option>を作る
    cur.execute("SELECT `ジャンル番号`,`ジャンル` FROM `genres` WHERE `ジャンル番号` BETWEEN 0 AND 15 ORDER BY `ジャンル番号` ")
    rows = cur.fetchall()
    rows.insert(0, {'ジャンル番号': 99, 'ジャンル': ''})  # 先頭に追加
    option_genre = []
    for row in rows:
        option_data = {}
        option_data['ジャンル番号'] = row['ジャンル番号']
        option_data['ジャンル'] = row['ジャンル']
        if row['ジャンル番号'] == nav_genre:
            option_data['selected'] = 'selected'
        else:
            option_data['selected'] = ''
        option_genre.append(option_data)

    cur.close()
    conn.close()

    return option_genre
# ---------------------------------------------------------------------------


@router.get('/get_option_service_id/{service_type}')
def get_option_service_id(service_type: str):
    '''サービスタイププルダウンメニューに合わせてサービスIDの option を返す

    サービスタイプが変わったときにAjaxで呼び出される
    - service_type : サービスのタイプ  (NO | GR | BS | CS)
    - return : サービスプルダウンメニューの中身
    '''

    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    sql = ("SELECT `サービスID`,`サービス名` "
           "FROM `channels` "
           "WHERE (`タイプ` = %s) AND (`有効` = 'checked') "
           "ORDER BY `表示順` , `チャンネル` , `サービスID` ")
    cur.execute(sql, (service_type,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    no_service = {"サービスID": 0, "サービス名": ""}        # NOのサービス
    rows.insert(0, no_service)

    option_service_id = []
    for row in rows:
        option_service_id.append(f'<option value="{row['サービスID']}">{row['サービス名']}</option>')

    return option_service_id    # リストで返すけれども $.html(data) がうまく処理してくれている
# --------------------------------------------------


def get_option_service_id_selected(service_type: str, service_id: int = 0):
    '''サービスタイプに合わせてサービスIDの option を返す
    - service_type : サービスのタイプ  (NO | GR | BS | CS)
    - service_id : selectされたサービスID
    - return : サービスプルダウンメニューの中身
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    sql = ("SELECT `サービスID`,`サービス名` "
           "FROM `channels` "
           "WHERE (`タイプ` = %s) AND (`有効` = 'checked') "
           "ORDER BY `表示順` , `チャンネル` , `サービスID` ")
    cur.execute(sql, (service_type,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    no_service = {"サービスID": 0, "サービス名": ""}        # NOのサービス
    rows.insert(0, no_service)

    option_service_id = []
    for row in rows:
        option_data = {}
        option_data['サービスID'] = row['サービスID']
        option_data['サービス名'] = row['サービス名']
        if row['サービスID'] == service_id:
            option_data['selected'] = 'selected'
        else:
            option_data['selected'] = ''
        option_service_id.append(option_data)

    return option_service_id
# --------------------------------------------------


@router.get('/get_detail/{id}')
def get_detail(id: int):
    '''番組の詳細情報を返す
    - id : 番組ID
    - return : dialogに表示する内容(HTML)
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    # 録画予約していないデータのための標準設定
    sql = ("SELECT * , `programs`.`ID` AS ProgID  , `programs`.`録画マージン前` AS margin_before , "
           "`programs`.`録画マージン後` AS margin_after ,`programs`.`ジャンル番号` AS genre "
           "FROM `programs` "
           "LEFT JOIN `channels`  ON (`programs`.`サービスID`   = `channels`.`サービスID`) "
           "LEFT JOIN `genres`    ON (`programs`.`ジャンル番号` = `genres`.`ジャンル番号`) "
           "LEFT JOIN `automatic` ON (`programs`.`自動予約ID`   = `automatic`.`ID`) "
           "WHERE `programs`.`ID`=%s ")
    cur.execute(sql, (id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    row['放送日時'] = f"{row['開始時刻'].strftime('%m月%d日(%a)')} {row['開始時刻'].strftime('%H:%M')} - {row['終了時刻'].strftime('%H:%M')}"

    if row['予約'] is None:
        row['録画予約'] = "予約なし"
        row['margin_before'] = config.margin_before
        row['margin_after'] = config.margin_after
    elif row['予約'] == '○':
        row['録画予約'] = "予約"
    else:
        row['録画予約'] = "予約無効"

    if row['保存ファイル名'] is None:
        row['保存ファイル名'] = g92.make_save_file_name(row, config.save_macro)

    if row['キーワード'] is not None:
        row['自動予約キーワード'] = '  (自動予約キーワード : 「' + row['キーワード'] + '」)'
    else:
        row['自動予約キーワード'] = ""

    row['拡張情報'] = row['拡張情報'].replace("\r\n", "&nbsp;").replace("\n", "<br>\n")  # 空白と改行を入れて表示したい

    # ダイアローグに表示するボタン作成
    # displayプロパティーを inline , none に設定する
    row['ボタン'] = {}
    row['ボタン']['中止'] = 'none'    # 初期値は none とし、必要なものを inline にする
    row['ボタン']['録画'] = 'none'
    row['ボタン']['変更'] = 'none'
    row['ボタン']['予約'] = 'none'
    row['ボタン']['削除'] = 'none'
    row['ボタン']['有効'] = 'none'
    row['ボタン']['無効'] = 'none'

    # 放送前の番組
    if row['開始時刻'] > datetime.datetime.now():
        # 予約の状態
        # 自動予約ID is     None  予約 None | ○ | ×        # 自動予約ではない
        # 自動予約ID is not None  予約        ○ | ×        # 自動予約の対象
        if row['自動予約ID'] is None:
            match row['予約']:
                case '○':
                    row['ボタン']['変更'] = 'inline'
                    row['ボタン']['削除'] = 'inline'
                    row['ボタン']['無効'] = 'inline'
                case '×':
                    row['ボタン']['予約'] = 'inline'
                    row['ボタン']['削除'] = 'inline'
                case None:
                    row['ボタン']['予約'] = 'inline'
                    row['ボタン']['無効'] = 'inline'
        else:
            match row['予約']:
                case '○':
                    row['ボタン']['変更'] = 'inline'
                    row['ボタン']['無効'] = 'inline'
                case '×':
                    row['ボタン']['有効'] = 'inline'

    # 放送中の番組
    if row['開始時刻'] < datetime.datetime.now() and row['終了時刻'] > datetime.datetime.now():
        if g94.is_recording(id):
            row['ボタン']['中止'] = 'inline'
        else:
            row['ボタン']['録画'] = 'inline'

    # 放送後の番組のボタンは「閉じる」のみ

    # 返信データ作成
    template = env_j2.get_template('html20.j2')
    program_detail = template.render(detail=row)

    # データを返す
    return HTMLResponse(content=program_detail)
# --------------------------------------------------
