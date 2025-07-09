# ---------------------------------------------------------------------------
# 録画タスク管理ルーチン
# ---------------------------------------------------------------------------
import datetime
import logging

from fastapi import APIRouter
import mysql.connector as mydb

from prog import g92, g93, config

router = APIRouter(tags=['録画タスク管理'])
# ---------------------------------------------------------------------------


@router.get('/rec_task_status')
def rec_task_status():
    '''録画タスクの状態を出力する デバッグ用ルーチン
    - return : 録画タスクの状態
    '''
    returns_dict = {}
    for key, rec_task in config.rec_task_list.items():
        returns_dict[key] = f'{rec_task.task_is_running()} , {rec_task.start_str} , {rec_task.rectime} , {rec_task.destfile} '
    return returns_dict
# ---------------------------------------------------------------------------


@router.get('/register_all_reservations')
def register_all_reservations():
    '''録画予約で、開始時刻が未来のものだけ新しいタスクを作る

    `programs` の (`予約` = '○') AND (`開始時刻`> NOW()) をRecTaskに登録する

    config.rec_task_list{}は初期化しない
    - return : 作成したタスクの数
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    # 番組情報取得
    sql = ("SELECT * , `programs`.`ID` AS ProgID , `programs`.`サービスID` AS sid "
           "FROM `programs` "
           "LEFT JOIN `channels` ON (`programs`.`サービスID` = `channels`.`サービスID`) "
           "WHERE (`予約` = '○') AND (`開始時刻` > NOW()) ")
    cur.execute(sql)
    programs = cur.fetchall()
    cur.close()
    conn.close()

    # 録画予約で、開始時刻が未来のものだけ新しいタスクを作る
    for program in programs:
        rec_task_create(program)

    return len(programs)
# ---------------------------------------------------------------------------


@router.get('/make_rec_task/{id}')
def make_rec_task(id: int):
    '''録画タスクを作る
    - id : 番組ID
    '''
    del_rec_task(id)    # 予約タスクの変更 すでに登録されている予約があれば削除して新しく予約タスクを作る

    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)
    # 番組情報取得
    sql = ("SELECT * , `programs`.`ID` AS ProgID , `programs`.`サービスID` AS sid "
           "FROM `programs` "
           "LEFT JOIN `channels` ON (`programs`.`サービスID` = `channels`.`サービスID`) "
           "WHERE `programs`.`ID` = %s")
    cur.execute(sql, (id,))
    program = cur.fetchone()
    cur.close()
    conn.close()

    rec_task_create(program)
# ---------------------------------------------------------------------------


def rec_task_create(program):
    '''番組情報から録画タスクを作って rec_task_list に登録する
    - program : 番組情報 + `programs`.`ID` AS ProgID , `programs`.`サービスID` AS sid
    '''
    # 録画パラメータ作成
    ProgID = program['ProgID']
    if program['開始時刻'] > datetime.datetime.now():
        start_at = program['開始時刻'] - datetime.timedelta(seconds=program['録画マージン前'])            # 開始時刻
        rectime = program['放送時間'] + program['録画マージン前'] + program['録画マージン後']             # 録画時間
    else:
        start_at = datetime.datetime.now()
        dt = program['終了時刻'] - datetime.datetime.now()
        rectime = dt.seconds + program['録画マージン後']
    sid = program['sid']
    type_ch = program['タイプ'] + '/' + program['チャンネル']
    destfile = config.save_root + '/' + program['保存ファイル名']
    args = (config.mirakurun_ip, config.mirakurun_port, sid, type_ch, rectime, destfile)                   # rivarunパラメータ
    # 録画タスク生成
    config.rec_task_list[ProgID] = g93.RecTask(ProgID, start_at, args, program['録画マージン前'])    # どこからも参照されなくなると、pythonのランタイムが消してくれるはず
# ---------------------------------------------------------------------------


@router.get('/del_rec_task/{id}')
def del_rec_task(id: int):
    '''録画タスクを削除する
    - id : 番組ID
    - return : {"result":処理結果(True|False) , "id":削除した番組ID}
    '''
    if config.rec_task_list.get(id) is None:
        return {"result": False, "id": None}
    config.rec_task_list[id].stop_task()            # タスクを止める。録画中ならば録画も停止
    config.rec_task_list.pop(id)                    # 録画タスククラスの配列から削除 --> pythonランタイムがオブジェクトを削除してくれるはず

    return {"result": True, "削除した番組ID": id}
# ---------------------------------------------------------------------------


@router.get('/del_all_rec_task')
def del_all_rec_task():
    '''すべての録画タスクを取り消す
    - return : 削除したタスクの数
    '''
    count = 0
    for key in list(config.rec_task_list.keys()):    # https://daiichi.dev/?p=43 (2024/03/06)
        config.rec_task_list[key].stop_task()        # タスクを止める。録画中ならば録画も停止
        config.rec_task_list.pop(key)
        count += 1
    return count
# ---------------------------------------------------------------------------


@router.get('/remove_used_task')
def remove_used_task():
    '''使用済み録画タスクを config.rec_task_list から削除する
    - return : 削除したタスクの数
    - link https://srbrnote.work/archives/2956#toc7 (2024/02/26)
    '''
    count = 0
    for key in list(config.rec_task_list.keys()):
        task_status = config.rec_task_list[key].task_is_running()
        if task_status == '削除済' or task_status == '録画後':        # 何らかの原因で残っているタスク
            config.rec_task_list.pop(key)
            count += 1
        if task_status == '録画前':                                   # 何らかの原因で実行されなかったタスク
            time_obj = datetime.datetime.strptime(config.rec_task_list[key].start_str, "%Y-%m-%d %H:%M:%S")
            if time_obj < datetime.datetime.now():
                config.rec_task_list[key].cancel_task()
                config.rec_task_list.pop(key)
                count += 1
    return count
# ---------------------------------------------------------------------------


@router.get('/is_recording/{id}')
def is_recording(id: int):
    '''録画中かどうか
    - id : 番組ID
    - return : (True 録画中 | False 録画中ではない)
    '''
    if id in config.rec_task_list:
        if config.rec_task_list[id].task_is_running() == '録画中':    # 録画している
            return True
    return False
# ---------------------------------------------------------------------------


@router.get('/remove_not_run_task')
def remove_not_run_task():
    '''現在録画中でないタスクを config.rec_task_list から削除する
    - return : 残っているタスク(録画中)の数
    '''
    for key in list(config.rec_task_list.keys()):
        if config.rec_task_list[key].task_is_running() != '録画中':
            config.rec_task_list[key].cancel_task()        # スケジューラーをキャンセルして、
            config.rec_task_list.pop(key)                  # リストから削除する -> pythonのランタイムによって、オブジェクトも削除されるはず。
    return len(config.rec_task_list)
# ---------------------------------------------------------------------------


def set_recording_status(id: int, status: str):
    '''録画状況をデータベースに記録する
    - id : 番組ID
    - status : 録画状況
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    cur.execute("UPDATE `programs` SET `録画状況` = %s WHERE ID = %s", (status, id))

    cur.close()
    conn.close()
# ---------------------------------------------------------------------------


@router.get('/rebuild_reserved')
def rebuild_reserved():
    '''番組予約再構築
    - return : '更新件数' , '内有効予約' , '内無効予約' , '録画中' , '作成タスク数'
    '''
    # 現在録画中でないタスクを削除する
    remain_num = remove_not_run_task()

    # 毎月１日には automatic のIDを付け直す
    today = datetime.datetime.now().day
    if today == 1:
        conn = mydb.connect(**config.database)
        cur = conn.cursor(dictionary=True)
        # https://shattered-blog.com/archives/4972 (2025/01/18)
        cur.execute("set @n:=0; update`automatic` set ID=@n:=@n+1;ALTER TABLE `automatic` auto_increment = 1;")
        cur.close()
        conn.close()
        logging.info('automaticテーブルID再編成')

    # automaticテーブルを元に、programsテーブルの自動予約IDを付け直す
    result = set_automatic_id()     # return : "予約更新件数" , "内有効予約" , "内無効予約"

    # 録画タスクを作る
    result['作成タスク数'] = register_all_reservations()
    result['録画中'] = remain_num

    logging.info(f"予約更新件数 = {result['予約更新件数']} (内有効予約件数 = {result['内有効予約']} , 内無効予約件数 = {result['内無効予約']})")
    return result
# --------------------------------------------------


def set_automatic_id():
    '''`programs`.`自動予約ID`をすべて NULL にして、`automatic`テーブルの情報を関連付ける
    - return : "予約更新件数" , "内有効予約" , "内無効予約"
    '''
    conn = mydb.connect(**config.database)
    cur = conn.cursor(dictionary=True)

    cur.execute("UPDATE `programs` SET `自動予約ID` = NULL ")               # すべてのデータについて自動予約設定との関連を切る

    cur.execute("SELECT * FROM `automatic` ORDER BY `更新日時` DESC ")      # 自動予約設定を読み出す
    automatics = cur.fetchall()

    # 予約する sql (`予約`がNULLの場合)
    sql_a = ("UPDATE `programs` "
             "SET `予約` = '○' , `自動予約ID` = %s , "
             "`録画マージン前` = %s , `録画マージン後` = %s , `保存ファイル名` = %s "
             "WHERE `ID` = %s ")
    # 自動予約IDを変更する sql (`予約`に○か×が入っている場合、自動予約IDのみ更新する)
    sql_b = ("UPDATE `programs` "
             "SET `自動予約ID` = %s , "
             "`録画マージン前` = %s , `録画マージン後` = %s , `保存ファイル名` = %s "
             "WHERE `ID` = %s ")

    for automatic in automatics:
        # 番組検索条件
        param = {}
        param = ['%' + automatic['キーワード'] + '%']    # LIKE で検索する場合は単語の前後に % を付けておく
        if automatic['タイプ'] != 'NO':
            and_type = "AND (`channels`.`タイプ` = %s) "
            param.append(automatic['タイプ'])
        else:
            and_type = ""
        if automatic['サービスID'] != 0:
            and_service_id = "AND (`programs`.`サービスID` = %s) "
            param.append(automatic['サービスID'])
        else:
            and_service_id = ""
        if automatic['ジャンル番号'] != 99:
            and_genre = "AND (`programs`.`ジャンル番号` = %s) "
            param.append(automatic['ジャンル番号'])
        else:
            and_genre = ""

        # 自動予約設定に合う番組を検索する
        sql = ("SELECT * , `programs`.`ID` AS pid "
               "FROM `programs` "
               "LEFT JOIN `channels`  ON (`programs`.`サービスID` = `channels`.`サービスID`) "
               "LEFT JOIN `automatic` ON (`programs`.`自動予約ID` = `automatic`.`ID`) "
               "WHERE (`番組名` LIKE %s) "
               "AND (`有効` = 'checked') "
               "AND (`開始時刻` > NOW()) "
               f"{and_type} "
               f"{and_service_id} "
               f"{and_genre}")
        cur.execute(sql, param)
        programs = cur.fetchall()

        # 検索したすべての番組について、データベースの情報を更新する
        for program in programs:
            if program['保存ファイル名'] is None:
                program['保存ファイル名'] = g92.make_save_file_name(program, config.save_macro)  # 保存ファイル名を作る

            param = [automatic['ID'], automatic['録画マージン前'], automatic['録画マージン後'], program['保存ファイル名'], program['pid']]

            match program['予約']:
                case None:
                    cur.execute(sql_a, param)    # 予約する sqlを使う
                case '○':
                    cur.execute(sql_b, param)    # 自動予約IDを変更する sqlを使う。自動予約IDは上書きする
                case '×':
                    cur.execute(sql_b, param)

    # 予約更新件数
    sql_valid = "SELECT COUNT(*) AS valid FROM programs WHERE `予約` = '○' AND `開始時刻` > NOW() "
    cur.execute(sql_valid)
    ret = cur.fetchone()
    valid_count = ret['valid']

    sql_invalid = "SELECT COUNT(*) AS invalid FROM programs WHERE `予約` = '×' AND `開始時刻` > NOW() "
    cur.execute(sql_invalid)
    ret = cur.fetchone()
    invalid_count = ret['invalid']

    cur.close()
    conn.close()

    result = {}
    result["予約更新件数"] = valid_count + invalid_count
    result["内有効予約"] = valid_count
    result["内無効予約"] = invalid_count
    return result
# ---------------------------------------------------------------------------
