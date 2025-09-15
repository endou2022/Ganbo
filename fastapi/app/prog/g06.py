# ---------------------------------------------------------------------------
# 「番組情報更新」ルーチン
# ---------------------------------------------------------------------------
import requests
import logging
import datetime
import json

from fastapi import APIRouter
import mysql.connector as mydb

from prog import g92, g94, config

router = APIRouter(tags=['番組情報更新'])
# --------------------------------------------------
# データ保存・更新のための SQL
'''
# https://hachi.hatenablog.com/entry/2020/05/07/235459 (2024/04/04)
# https://beyondjapan.com/blog/2016/02/replace-query/ (2024/04/04)
# https://www.united-bears.co.jp/blog/archives/2786 (2024/04/04)
# sql = ('REPLACE INTO `programs` (`ID` ,`イベントID` ,`サービスID` ,`ネットワークID` ,`開始時刻` ,`放送時間` ,`終了時刻` ,`フリー` ,`番組名` ,`説明` ,`ジャンル番号` ,`拡張情報` ) '
#                         'VALUES (%s   , %s          , %s          , %s              , %s        , %s        , %s        , %s      , %s      , %s    , %s            , %s ) ')
'''

# https://www.engilaboo.com/insert-on-duplicate-key-update/ (2024/01/11)
# https://linkers.hatenablog.com/entry/2022/03/09/131414 (2024/01/11)
# https://qiita.com/Yuki_Oshima/items/2a73cf70ccbf67bd5215 (2024/01/11)
# UPSERTのためのSQL文
upsert_sql = ('INSERT INTO `programs` (`ID` ,`イベントID` ,`サービスID` ,`ネットワークID` ,`開始時刻` ,`放送時間` ,`終了時刻` ,`フリー` ,`番組名` ,`説明` ,`ジャンル番号` ,`拡張情報` ) '
              '                VALUES (%s   , %s          , %s          , %s              , %s        , %s        , %s        , %s      , %s      , %s    , %s            , %s ) '
              'ON DUPLICATE KEY UPDATE '
              '`ID` = VALUES(`ID`)  , '
              '`イベントID` = VALUES(`イベントID`)  , '
              '`サービスID` = VALUES(`サービスID`)  , '
              '`ネットワークID` = VALUES(`ネットワークID`)  , '
              '`開始時刻` = VALUES(`開始時刻`)  , '
              '`放送時間` = VALUES(`放送時間`)  , '
              '`終了時刻` = VALUES(`終了時刻`)  , '
              '`フリー` = VALUES(`フリー`)  , '
              '`番組名` = VALUES(`番組名`)  , '
              '`説明` = VALUES(`説明`)  , '
              '`ジャンル番号` = VALUES(`ジャンル番号`)  , '
              '`拡張情報` = VALUES(`拡張情報`)  ')

'''
# https://zenn.dev/toranoko114/articles/fb76e0e7fcf7f7 (2024/01/11)
# https://dev.mysql.com/doc/refman/8.0/ja/insert-on-duplicate.html (2024/01/11)
# https://zenn.dev/drunkcoder1984/articles/ff39cd75bc748d (2024/01/11)
    'AS `new` '
    'ON DUPLICATE KEY UPDATE '
    '`ID` = `new`.`ID`  , '
    '`イベントID` = `new`.`イベントID`  , '
    '`サービスID` = `new`.`サービスID`  , '
    '`ネットワークID` = `new`.`ネットワークID`  , '
    '`開始時刻` = `new`.`開始時刻`  , '
    '`放送時間` = `new`.`放送時間`  , '
    '`終了時刻` = `new`.`終了時刻`  , '
    '`フリー` = `new`.`フリー`  , '
    '`番組名` = `new`.`番組名`  , '
    '`説明` = `new`.`説明`  , '
    '`ジャンル番号` = `new`.`ジャンル番号`  , '
    '`拡張情報` = `new`.`拡張情報`')
'''
# --------------------------------------------------


@router.get('/reflesh_programs')
def reflesh_programs():
    '''mirakurun から番組情報を得てデータベースを更新する
    - return : '番組情報' , '更新件数' , '名前変更' , '削除件数'
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    # データベースのコンテナの時間帯をJSTにしておく必要がある
    cur.execute("DELETE FROM `programs` WHERE (`終了時刻` < NOW() - INTERVAL 5 HOUR) ")        # 終了時刻が5時間以上前のデータを消す

    # 番組情報を取得するサービス
    cur.execute("SELECT `サービスID` FROM `channels` WHERE `有効` = 'checked' ")               # 有効にしているサービスだけ情報を得る
    channels = cur.fetchall()

    prog_num = 0
    chg_name = 0
    chg_prog = 0
    del_prog = 0
    # 番組取得 番組表に表示するサービスだけ繰り返す
    for channel in channels:
        programs, ret = get_programs(channel['サービスID'])    # サービスIDに関する番組素取得
        if programs == 'error':
            return {"result": False, "exception": ret}              # get_programs()で例外が発生した

        insert_lists, program_data, id_list = analize_programs(programs)       # mirakurun から得たJSON形式の番組情報をデータベースに入力できる形にする
        prog_num += len(insert_lists)
        chg_name += cahnge_save_name(program_data)                  # 番組名が変更されたら保存ファイル名も変更する
        cur.executemany(upsert_sql, insert_lists)                   # 番組情報をデータベースに格納する
        chg_prog += cur.rowcount                                    # insert_lists の数ではない

        # UPSERTのときに、リストにないデータの削除。ChatGPT(2024/12/27)に教えてもらった
        format_strings = ','.join(['%s'] * len(id_list))
        query = f"DELETE FROM `programs` WHERE (`ID` NOT IN ({format_strings})) AND (`サービスID` = %s) AND (`開始時刻` >= NOW()) "
        id_list.append(channel['サービスID'])
        cur.execute(query, id_list)
        del_prog += cur.rowcount                                    # 削除したデータ数

    cur.close()
    conn.close()

    logging.info('番組情報取得結果')
    logging.info(f'番組情報 = {prog_num} , 番組更新件数 = {chg_prog} , 名前変更 = {chg_name} , 削除件数 = {del_prog}')
    reflesh_result = {}
    reflesh_result['番組情報'] = prog_num   # console.table()用
    reflesh_result['番組更新件数'] = chg_prog
    reflesh_result['名前変更'] = chg_name
    reflesh_result['削除件数'] = del_prog

    rebuild_result = g94.rebuild_reserved()    # 番組予約再構築

    result = reflesh_result | rebuild_result
    result['result'] = True

    return result
# --------------------------------------------------


def get_programs(serviceId):
    '''番組情報を得る
    - serviceId : サービスID
    - return : 番組情報 , 番組件数または例外
    '''
    try:
        url = f"http://{config.mirakurun_ip}:{config.mirakurun_port}/api/programs?serviceId={serviceId}"        # mirakurun 番組情報取得API
        response = requests.get(url, timeout=5)            # https://atmarkit.itmedia.co.jp/ait/articles/2209/27/news035.html (2024/03/01)
        response.raise_for_status()
        # https://hirosetakahito.hatenablog.com/entry/2019/12/25/144159 (2025/09/13)
        # https://murasan-net.com/2021/12/31/2021-12-31-161241/ (2025/09/13)
        # json.load に入れてはいけない制御文字があった場合の対策
        programs = json.loads(response.text, strict=False)
        return_num = len(programs)
    except Exception as exp:
        logging.error(f'番組情報取得例外 {str(exp)}')
        programs = 'error'
        return_num = str(exp)

    return programs, return_num
# ---------------------------------------------------------------------------


def analize_programs(programs):
    '''mirakurun から得たJSON形式の番組情報をデータベースに入力できる形にする

    program_data 辞書型の番組情報。番組名が変更されたら保存ファイル名も変更する
    - programs : get_programs()で得たJSON形式の番組情報
    - return : insert_list データベースに入力できる番組情報
    - return : program_data 番組情報
    - return : id_list 番組のID
    '''
    insert_list = []
    program_data = []
    id_list = []
    for program in programs:
        insert_dict = {}                                                        # sql との関係から順番を変えてはいけない
        insert_dict['ID'] = program['id']                                       # ID
        insert_dict['イベントID'] = program['eventId']                          # イベントID
        insert_dict['サービスID'] = program['serviceId']                        # サービスID
        insert_dict['ネットワークID'] = program['networkId']                    # ネットワークID
        start_at = datetime.datetime.fromtimestamp(program['startAt'] / 1000)
        insert_dict['開始時刻'] = start_at.strftime('%Y-%m-%d %H:%M:%S')        # 開始時刻
        duration = datetime.timedelta(milliseconds=program['duration'])
        insert_dict['放送時間'] = duration.seconds                              # 放送時間
        end_at = start_at + duration
        insert_dict['終了時刻'] = end_at.strftime('%Y-%m-%d %H:%M:%S')          # 終了時刻
        if program['isFree']:                                                   # フリー
            insert_dict['フリー'] = 'True'
        else:
            insert_dict['フリー'] = 'False'
        if 'name' in program:                                                   # 番組名
            insert_dict['番組名'] = program['name']
        else:
            insert_dict['番組名'] = '---'
        if 'description' in program:                                            # 説明
            insert_dict['説明'] = program['description']
        else:
            insert_dict['説明'] = '---'
        if 'genres' in program:
            lv1 = program['genres'][0]['lv1']
            insert_dict['ジャンル番号'] = lv1                                   # ジャンル番号
        else:
            insert_dict['ジャンル番号'] = 15
        if 'extended' in program:                                               # 拡張情報
            ext = ""
            items = program['extended'].items()
            for key, val in items:
                ext += key + "：" + val + "\n"                                  # 「主演」の区切り
        else:
            ext = "---"
        insert_dict['拡張情報'] = ext

        insert_list.append(list(insert_dict.values()))                          # データベースへの入力はリストで行う
        program_data.append(insert_dict)
        id_list.append(program['id'])

    return insert_list, program_data, id_list
# ---------------------------------------------------------------------------


def cahnge_save_name(program_data):
    '''番組名が変更されたら保存ファイル名も変更する
    - program_data : 辞書型の番組情報
    - return : 修正した件数
    '''
    ret_count = 0
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    sql = ("UPDATE `programs` "
           "SET `保存ファイル名` = %s "
           "WHERE (`ID` = %s) "
           "AND (`番組名` != %s) "
           "AND (`予約` IS NOT NULL)")

    for program in program_data:
        # make_save_file_name()で使えるデータにする
        program['開始時刻'] = datetime.datetime.strptime(program['開始時刻'], '%Y-%m-%d %H:%M:%S')    # datetimeに戻しておく
        program['終了時刻'] = datetime.datetime.strptime(program['終了時刻'], '%Y-%m-%d %H:%M:%S')
        cur.execute("SELECT * FROM `channels` WHERE `サービスID` = %s ", (program['サービスID'],))
        service = cur.fetchone()
        program['サービス名'] = service['サービス名']

        save_name = g92.make_save_file_name(program, config.save_macro)
        cur.execute(sql, (save_name, program['ID'], program['番組名']))
        ret_count += cur.rowcount

    cur.close()
    conn.close()

    return ret_count
# ---------------------------------------------------------------------------


def get_program_by_id(pid: int, destfile: str):
    '''IDで示される番組情報を得る
    - pid : 番組情報ID
    - destfile : 保存ファイル名
    - return : 番組情報
    '''
    try:
        url = f"http://{config.mirakurun_ip}:{config.mirakurun_port}/api/programs/{pid}"         # mirakurun 番組情報取得API
        response = requests.get(url, timeout=5)
        if response.status_code != 200:     # 番組が見つからなかった
            return None
        response.raise_for_status()
    except Exception as exp:
        logging.error(f'番組情報取得例外 {str(exp)}')
        program = None

    program = json.loads(response.text, strict=False)                  # 番組情報解析　g06.analize_programs() の一部
    program['ID'] = program['id']                                       # ID
    start_at = datetime.datetime.fromtimestamp(program['startAt'] / 1000)
    program['start_at'] = start_at
    program['開始時刻'] = start_at.strftime('%Y-%m-%d %H:%M:%S')        # 開始時刻
    duration = datetime.timedelta(milliseconds=program['duration'])
    program['放送時間'] = duration.seconds                              # 放送時間
    end_at = start_at + duration
    program['終了時刻'] = end_at.strftime('%Y-%m-%d %H:%M:%S')          # 終了時刻

    return program
# ---------------------------------------------------------------------------


def update_program(program):
    '''番組情報更新
    - program 番組情報
    - return 更新された番組情報
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    sql = "UPDATE `programs` SET `開始時刻` = %s , `放送時間` = %s , `終了時刻` = %s WHERE `ID` = %s"
    param = (program['開始時刻'], program['放送時間'], program['終了時刻'], program['ID'])
    cur.execute(sql, param)

    sql = ("SELECT * , `programs`.`ID` AS ProgID , `programs`.`サービスID` AS sid "
           "FROM `programs` "
           "LEFT JOIN `channels` ON (`programs`.`サービスID`   = `channels`.`サービスID`) "
           "LEFT JOIN `genres`   ON (`programs`.`ジャンル番号` = `genres`.`ジャンル番号`) "
           "WHERE `programs`.`ID` = %s ")
    cur.execute(sql, (program['ID'],))
    program = cur.fetchone()

    cur.close()
    conn.close()

    return program
# ---------------------------------------------------------------------------
