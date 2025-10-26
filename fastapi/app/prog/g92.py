# ---------------------------------------------------------------------------
# 共通ルーチン
# ---------------------------------------------------------------------------
import datetime
import re
import unicodedata

import mysql.connector as mydb
from fastapi import APIRouter
from jinja2 import Environment, FileSystemLoader

from prog import config, g94

env_j2 = Environment(loader=FileSystemLoader('./templates'), autoescape=True)
router = APIRouter(tags=['共通ルーチン2'])
# ---------------------------------------------------------------------------


@router.get('/toggle_reserve/{id}')
def toggle_reserve(id: int):
    '''予約状況を反転させる
    * `自動予約ID` == NULLの場合 `予約` -> '○' , '×' , NULLのトグル
    * `自動予約ID` == 番号の場合 `予約` -> '○' , '×'のトグル
    - id : 番組ID
    - return : {'can_not_change' : (True | False) , 'is_start' : ()'0' 録画予約 | '1' 録画開始) , 'reserve_str' : (○ | × | None)}
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    sql = ("SELECT * , `programs`.`ID` AS ProgID "
           "FROM `programs` "
           "LEFT JOIN `channels` ON (`programs`.`サービスID` = `channels`.`サービスID`) "        # 保存ファイル名にサービス名を使うかもしれないので結合している
           "WHERE `programs`.`ID` = %s ")
    cur.execute(sql, (id,))
    row = cur.fetchone()

    cur.close()
    conn.close()
    if row['終了時刻'] < datetime.datetime.now():    # すでに終了している
        return {'can_not_change': True, 'reserve_str': row['予約']}
    if row['録画状況'] == '録画中':
        return {'can_not_change': True, 'reserve_str': row['予約']}

    # 予約に関するデータ
    reserve_data = {}
    reserve_data['id'] = row['ProgID']
    reserve_data['detail_before'] = row['録画マージン前']
    reserve_data['detail_after'] = row['録画マージン後']
    if row['保存ファイル名'] is None:
        reserve_data['file_name'] = make_save_file_name(row, config.save_macro)
    else:
        reserve_data['file_name'] = row['保存ファイル名']

    # `自動予約ID` == NULLの場合 `予約` -> '○' , '×' , NULLのトグル
    # `自動予約ID` == 番号の場合 `予約` -> '○' , '×'のトグル
    if row['自動予約ID'] is None:
        match row['予約']:
            case '○':
                reserve_data['reserve'] = '×'
            case '×':
                reserve_data['reserve'] = None
            case None:
                reserve_data['reserve'] = '○'
    else:
        match row['予約']:
            case '○':
                reserve_data['reserve'] = '×'
            case '×':
                reserve_data['reserve'] = '○'

    return set_reserve(reserve_data)
# ---------------------------------------------------------------------------


@router.post('/set_reserve')
def set_reserve(reserve_data: dict):
    '''番組予約を設定する
    - reserve_data 予約に関するデータ
    - reserve_data['id'] : 番組ID
    - reserve_data['reserve'] : 設定する予約 ('○' | '×' | None)
    - reserve_data['detail_before'] : 録画マージン前
    - reserve_data['detail_after'] : 録画マージン後
    - reserve_data['file_name'] : 保存ファイル名
    - return : {設定状況('is_start'): ('0' 録画予約 | '1' 録画開始) , 録画設定('reserve_str') : (○ | × | None)}
    '''
    # ファイル名を整える
    f_name = change_allow_char(unicode_normalize(remove_ARIB(reserve_data['file_name'])))

    # データベースを操作する
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    sql = "UPDATE `programs` SET `予約` = %s , `録画マージン前` = %s , `録画マージン後` = %s , `保存ファイル名` = %s WHERE `ID` = %s "
    param = [reserve_data['reserve'], reserve_data['detail_before'], reserve_data['detail_after'], f_name, reserve_data['id']]
    cur.execute(sql, param)

    if reserve_data['reserve'] == '○':
        sql = "SELECT `開始時刻` < NOW() AS is_start FROM `programs` WHERE `ID` = %s "
        cur.execute(sql, (reserve_data['id'],))
        row = cur.fetchone()
    else:
        row = {'is_start': 0}

    cur.close()
    conn.close()

    # 録画タスクを操作する
    match reserve_data['reserve']:
        case '○':
            g94.make_rec_task(int(reserve_data['id']))    # reserve_data['id']は string なので int に返還する必要がある。インタプリタだからと入って勝手に変換してくれない
        case '×':
            g94.del_rec_task(int(reserve_data['id']))
        case None:
            g94.del_rec_task(int(reserve_data['id']))

    return {'is_start': row['is_start'], 'reserve_str': reserve_data['reserve']}
# ---------------------------------------------------------------------------


def search_programs(key_word: str, search_data: dict, free_flag: bool = False, word: str = ''):
    '''条件に合った番組を検索する(search_data はすべて文字列で来る)
    - key_word : キーワード
    - search_data['service_type'] : サービスのタイプ  (NO | GR | BS | CS)
    - search_data['service_id'] : サービスID=0の場合は指定なし
    - search_data['genre'] : ジャンル番号=99の場合は指定なし
    - free_flag : g04.search_prog()からのリクエストを受ける
    - word : g04.search_prog()の自由キーワード
    - return : 検索したデータのリスト
    '''
    '''
    g04.search_prog()だけは、どんなキーワードが送られてくるか分からないので、sql文にkey_wordを直接入力してはいけない。
    SQLインジェクションだった(2025/07/02まで)。
    「'」を含む文字列を検索しているときにエラーが出たので気づいた。
    '''
    '''
    ※重要な注意※
    `番組名` LIKE '%キーワード%' で検索をかけるとき、
    1)`番組名`カラムの照合順序が utf8mb4_unicode_ci の場合、
      大文字・小文字、全角・半角、ひらがな・カタカナ、濁音・半濁音をすべて区別しないで検索してくれるので便利そうだが、
      キーワードが入っていないデータも拾ってきてしまう。
      ex.
      キーワードを「ドイツ」とすると、「おかあさんといっしょ」も検索される。（「サンドイッチ」も検索される）
                                                  ^^^^^^                            ^^^^^^
      utf8mb4_general_ci ならば間違った検索はしないが、全角・半角、ひらがな・カタカナ、濁音・半濁音を区別する。
    2)utf8mb4_unicode_ci の場合、ARIB外字の 🈟 , 🈡 を検索してくれるが、
      utf8mb4_general_ci では、ほかのARIB外字も一緒に拾ってきてしまう（🈟 , 🈡を正確に検索できない）
    ※照合順序は utf8mb4_unicode_ci とする※
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    # 条件設定
    param = []
    if free_flag:
        param.append(f"%{word}%")                   # LIKEを使う場合はsql文の外で % を付けておく
    if search_data['service_type'] == 'NO':         # サービスタイプの絞りなし
        and_type = ""
    else:
        and_type = "AND (`channels`.`タイプ` = %s) "
        param.append(search_data['service_type'])

    if search_data['service_id'] == '0':           # サービスの絞りなし
        and_service = ""
    else:
        and_service = "AND (`programs`.`サービスID` = %s) "
        param.append(search_data['service_id'])

    if search_data['genre'] == '99':               # ジャンルの絞りなし
        and_genre = ""
    else:
        and_genre = "AND (`programs`.`ジャンル番号` = %s) "
        param.append(search_data['genre'])

    # 検索
    program_list = []
    sql = ("SELECT * , `programs`.`ID` AS ProgID , `programs`.`サービスID` AS sid "
           "FROM `programs` "
           "LEFT JOIN `channels`  ON (`programs`.`サービスID`   = `channels`.`サービスID`) "
           "LEFT JOIN `genres`    ON (`programs`.`ジャンル番号` = `genres`.`ジャンル番号`) "
           "LEFT JOIN `automatic` ON (`programs`.`自動予約ID`   = `automatic`.`ID`) "
           f"WHERE ({key_word}) "
           "AND (`終了時刻` > NOW()) "
           "AND (`有効` = 'checked') "
           f"{and_type} "
           f"{and_service} "
           f"{and_genre} "
           "ORDER BY `開始時刻` , `表示順` , `チャンネル` , `channels`.`サービスID` ")
    cur.execute(sql, param)
    programs = cur.fetchall()

    # 一覧表データ整形
    if cur.rowcount >= 1:
        for program in programs:
            data = {}
            data['放送日'] = program['開始時刻'].strftime('%m月%d日(%a)')
            data['ID'] = program["ProgID"]
            data['自動予約'] = program['キーワード'] if program['自動予約ID'] is not None else "-"
            data['予約状況'] = '-' if program['予約'] is None else program['予約']
            data['サービス名'] = program["サービス名"]
            data['時間'] = f'{program["開始時刻"].strftime("%H:%M")} - {program["終了時刻"].strftime("%H:%M")}'
            if data['予約状況'] != '○':
                data['rec_status'] = 'not_reserved'
            else:
                data['rec_status'] = ''
            if program['録画状況'] == '録画中':
                data['rec_status'] = "on_recording"
            data['番組名'] = program["番組名"]
            data['終新フラグ'] = ""
            if ('🈟' in program["番組名"]):
                data['終新フラグ'] = '🈟'
            if ('🈠' in program["番組名"]):
                data['終新フラグ'] = '🈠'
            if ('🈡' in program["番組名"]):
                data['終新フラグ'] = '🈡'
            data['保存ファイル名'] = program["保存ファイル名"]
            data['ジャンル'] = program['ジャンル']
            program_list.append(data)

    cur.close()
    conn.close()

    return program_list
# --------------------------------------------------


def remove_ARIB(org_str: str) -> str:
    '''ARIB外字は悪さしそうだからARIB外字を削除する
    - org_str 処理する文字列
    - return : 処理後の文字列
    '''
    arib_string = '[🅊🅌🄿🅆🅋🈐🈑🈒🈓🅂🈔🈕🈖🅍🄱🄽🈗🈘🈙🈚🈛⚿🈜🈝🈞🈟🈠🈡🈢🈣🈤🈥🅎㊙🈀]'
    return re.sub(arib_string, '', org_str)
# ---------------------------------------------------------------------------


def unicode_normalize(org_str: str) -> str:
    '''文字列をUnicode正規化する
    - org_str 処理する文字列
    - return : 処理後の文字列
    - link https://note.nkmk.me/python-unicodedata-normalize/ (2024/01/28)
    '''
    '''
    NFKC を使うので、
    英数字 -> 半角
    半角カタカナ -> 全角
    ASCII文字 -> 半角
    カギカッコや句読点など -> 全角
    各種合成済み文字(㈱㌖など) -> 分解・変換
    ～（全角チルダ: U+FF5E）は~（半角チルダ: U+007E）に変換されるが、
    〜（波ダッシュ: U+301C）は変換されない。
    '''
    return unicodedata.normalize('NFKC', org_str)
# ---------------------------------------------------------------------------


def change_allow_char(org_str: str) -> str:
    '''文字列からからOSのファイル名としてふさわしくない文字を全角にしてしまう
    1. 文字列前後の空白文字を削除
    2. 文字列前のピリオドを削除
    Windowsの予約語(CON,PRN,AUX...)をチェックしていない
    - org_str 処理する文字列
    - return : 処理後の文字列
    '''
    replace_str = {
        "\t": "",
        "\\": "￥",
        "/": "／",
        ":": "：",
        "*": "＊",
        "?": "？",
        '"': "”",
        ">": "＞",
        "<": "＜",
        "|": "｜",
        "〜": "～",    # 〜(波ダッシュ)は禁止文字ではないが扱いが悪いので ～ (全角チルダ)に変換する
        "~": "～"      # ~ は見にくいので ～ (全角チルダ)に変換する
    }
    return org_str.translate(str.maketrans(replace_str)).strip().strip('.')
# ---------------------------------------------------------------------------


def make_save_file_name(name_param: dict, macro: str) -> str:
    '''マクロを展開し保存するファイル名を作る

    変換できるマクロは
        $Title$ : 番組名
        $date$ : 放送日(%Y-%m-%d)
        $time$ : 開始時刻(%H%M%S)
        $datetime$ : 放送日時(%Y-%m-%d %H%M%S)
        $ServiceName$ : サービス名
    - name_param ファイル名を作るデータ
    - name_param['番組名']
    - name_param['開始時刻']
    - name_param['サービス名']
    - macro マクロ文字列
    - return : ファイル名
    '''
    d = name_param['開始時刻'].strftime('%Y-%m-%d')
    t = name_param['開始時刻'].strftime('%H%M%S')
    dt = name_param['開始時刻'].strftime('%Y-%m-%d %H%M%S')
    f_name = macro.replace('$Title$', name_param['番組名']).replace('$date$', d).replace('$time$', t).replace('$datetime$', dt).replace('$ServiceName$', name_param['サービス名'])
    return change_allow_char(unicode_normalize(remove_ARIB(f_name)))
# ---------------------------------------------------------------------------
