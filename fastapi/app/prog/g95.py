# ---------------------------------------------------------------------------
# 「定時刻番組情報更新」ルーチン
# ---------------------------------------------------------------------------
import threading
import time

import mysql.connector as mydb
import schedule  # 外部モジュールのスケジューラ。指定時刻に繰り返してタスクを実行する

from prog import config, g06

# --------------------------------------------------


def start_schedule():
    '''scheduleモジュールを実行するスレッドを開始'''
    set_schedule(None)
    thread = threading.Thread(target=wait_schedule, daemon=True)
    thread.start()
# --------------------------------------------------


def set_schedule(time_str: str = '04:05'):
    '''番組情報更新時刻を設定する
    - time_str : 時刻の文字列 , None の場合はデータベースから引いてくる
    '''
    if time_str is None:
        conn = mydb.connect(**config.database)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM `setting` WHERE `キー` = '番組情報更新時刻' ",)
        row = cur.fetchone()
        cur.close()
        conn.close()
        time_str = row['値']

    schedule.clear()
    schedule.every().day.at(time_str).do(g06.reflesh_programs)
# --------------------------------------------------


def wait_schedule():
    '''スケジューラーの実行待ちルーチン(スレッド内で動かす)'''
    while True:
        schedule.run_pending()
        time.sleep(60)
# --------------------------------------------------


def clear_schedule():
    '''スケジューラーをクリアする'''
    schedule.clear()
# --------------------------------------------------
