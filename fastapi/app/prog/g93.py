# ---------------------------------------------------------------------------
# RecTask Class  スレッドを使って録画を管理するクラス
# ---------------------------------------------------------------------------
# 汎用のクラスにはしていない＝パラメータチェックなし、エラー処理なし、外部のファイルにも依存している
# concurrent.futures.ThreadPoolExecutor が threading.Thread の上位互換というが、
# メインスレッドを停止したときに、サブスレッドが停止してくれないので、今回は利用しなかった
# ---------------------------------------------------------------------------
import datetime
import logging
import sched  # 組み込みモジュールのイベントスケジューラ。指定時刻にタスクを起動する
import subprocess
import threading
import time
from os.path import splitext

from prog import config, g06, g94

# ---------------------------------------------------------------------------


class RecTask():
    '''スレッドを使って録画を管理するクラス'''

    def __init__(self, p_id: int, start_at: datetime, args: tuple, before_margin: int):
        '''コンストラクタ
            オブジェクト作成と同時にタスクを登録し、スケジューラを起動する。
        - p_id : 番組ID
        - start_at : タスク実行時刻。実行時刻の検査は呼び出し側で行う
        - args rivarun へ渡すパラメータ (host , port , sid , type_ch , rectime , destfile)
        - before_margin 録画マージン前、番組情報確認に利用
        '''
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.thread = threading.Thread(target=self.scheduler.run, daemon=True)        # daemon=Trueにすることで、メインスレッド終了時にサブスレッドも終了する
        self.proc = None
        self.returncode = None
        self.id = p_id                  # int
        self.start_at = start_at        # datetime
        self.host = args[0]             # str
        self.port = args[1]             # str
        self.sid = args[2]              # int
        self.type_ch = args[3]          # str
        self.rectime = args[4]          # int
        self.destfile = args[5]         # str
        self.start_str = start_at.strftime('%Y-%m-%d %H:%M:%S')
        self.before_margin = before_margin
        self.check_at = start_at - datetime.timedelta(minutes=config.check_at)          # 番組の時間が変更されていないか検査する時刻 = 1分前

        self.set_task()                 # タスク登録
        self.thread.start()
# -------------------------

    def set_task(self):
        '''タスクを登録する'''
        if self.check_at > datetime.datetime.now():
            self.scheduler.enterabs(self.check_at.timestamp(), 1, self.check_program)   # 番組検査タスク
        self.scheduler.enterabs(self.start_at.timestamp(), 2, self.run_rivarun)         # 録画タスク
        g94.set_recording_status(self.id, '録画予約')
# -------------------------

    def cancel_task(self):
        '''実行前のタスクをすべてキャンセルする。
        scheduler.run() で実行してしまったタスクは操作できない
        '''
        for event in self.scheduler.queue:
            self.scheduler.cancel(event)

        g94.set_recording_status(self.id, '予約解除')
# -------------------------

    def stop_task(self):
        '''録画タスクを止める。

        録画タスクが実行前ならば、録画タスクキャンセル、サブプロセスが動いているのならば、サブプロセス停止
        '''
        self.cancel_task()
        if self.proc is not None:
            if self.proc.poll() is None:    # サブプロセスが動いているのならば、サブプロセス停止
                self.proc.kill()
                self.returncode = self.proc.poll()
                if self.returncode is None:
                    self.returncode = -1
                logging.info(f'録画中断 : {self.id} , {self.destfile} , returncode = {self.returncode}')
                g94.set_recording_status(self.id, '録画中断')
            else:
                self.returncode = self.proc.poll()
                # logging.info(f'録画終了済み : {self.id} , {self.destfile} , returncode = {self.returncode}')
# -------------------------

    def task_is_running(self):
        '''サブプロセスが動いているかどうか
        - return : ('削除済'(録画されることはない) | '録画前'(待機中) | '録画中' | '録画後'(強制終了も含む)  returncode()で戻り値がわかる)
        '''
        if self.proc is None and self.scheduler.empty():
            return '削除済'
        if not self.scheduler.empty():
            return '録画前'
        if self.proc.poll() is None:
            return '録画中'
        else:
            return '録画後'
# -------------------------

    def run_rivarun(self):
        '''rivarunをサブプロセスとして動かす'''
        '''
        Usage:
            rivarun [--b25] [--mirakurun host:port] [--priority priority] [--sid SID] [--ch type/channel] rectime destfile
            Remarks:
            * if rectime  is `-`, records indefinitely.
            * if destfile is `-`, stdout is used for output.
            * if `--sid` option specified, will ignore `--ch` option.
            Options:
            --b25:                 Send decode request
            --mirakurun host:port: Specify Mirakurun hostname and portnumber
            --priority priority:   Specify client priority (default=0)
            --sid SID:             Specify SID number
            --ch type/channel      Specify channeltype and channel
                                    type = GR | BS | CS | SKY
            --help:                Show this help
            --version:             Show version
            --list:                Show channel list
        ex.
            rivarun --b25 --mirakurun 192.168.11.75:40772 --sid 33840 --ch GR/23 30 test.ts
        '''
        # Popen() は起動したプログラムの終了を待たない。
        # poll() を使って状態を調べる, kill()で止める, wait()で終わるまで待つ
        try:
            logging.info(f'録画開始 : {self.id} , {self.destfile}')
            g94.set_recording_status(self.id, '録画中')
            # logging.info(f'rivarun --b25 --mirakurun {self.host}:{self.port} --sid {str(self.sid)} --ch {str(self.type_ch)} {str(self.rectime)} {str(self.destfile)}')
            self.proc = subprocess.Popen(['rivarun', '--b25', '--mirakurun', f'{self.host}:{self.port}', '--sid', str(
                self.sid), '--ch', str(self.type_ch), str(self.rectime), str(self.destfile)])    # すべて文字列で与える必要がある
            self.proc.wait()        # スレッド内で動いてるので、wait() してもメインプロセスは止まらない
            self.returncode = self.proc.poll()
            if self.returncode == 0:    # 0以外は中断されたと思われる
                logging.info(f'録画完了 : {self.id} , {self.destfile} , returncode = {self.returncode}')
                g94.set_recording_status(self.id, '録画完了')
                g94.del_rec_task(self.id)
        except Exception as e:
            # self.proc はNone のままなので、task_is_running() で検査すると '削除済' が返る
            logging.error(f'録画例外 : {self.id} , {self.destfile} , exception = {str(e)}')
            g94.set_recording_status(self.id, str(e))
            g94.del_rec_task(self.id)
# -------------------------

    def debug_task(self, count='30', id_str='TEST'):
        '''デバッグ用タスク'''
        try:
            logging.info(f'デバッグタスク開始 : {self.id} , {self.destfile}')
            g94.set_recording_status(self.id, '録画中')
            self.proc = subprocess.Popen(['python', '/app/prog/dummy.py', str(count), str(id_str)])
            self.proc.wait()
            self.returncode = self.proc.poll()
            if self.returncode == 0:
                logging.info(f'デバッグタスク終了 : {self.id} , {self.destfile} , returncode = {self.returncode}')
                g94.set_recording_status(self.id, '録画完了')
                g94.del_rec_task(self.id)
        except Exception as e:
            logging.error(f'デバッグタスク例外 : {self.id} , {self.destfile} , exception = {str(e)}')
            g94.set_recording_status(self.id, str(e))
            g94.del_rec_task(self.id)
# --------------------------------------------------

    def check_program(self):
        '''番組の開始時刻が変更されているかどうか調べる。
        変更されていたら録画タスクを作り直す
        '''
        program = g06.get_program_by_id(self.id, self.destfile)
        if program is None:             # 番組が存在しなければ、録画タスクを消して終わる
            logging.info(f'番組が見つからなかった {self.start_at} {self.destfile}')
            fname, _ = splitext(self.destfile)
            with open(fname + '.log', 'a') as file:
                file.write(f'番組が見つからなかった {self.start_at} {self.destfile}\n')
            g94.del_rec_task(self.id)
            return

        start_at = program['start_at'] - datetime.timedelta(seconds=self.before_margin)
        if self.start_at == start_at:
            return                      # 録画開始時刻に変更がなければ戻る (番組情報検査ルーチン終了)

        logging.info(f'番組開始時刻変更 {self.start_at} -> {start_at} {self.destfile}')
        fname, _ = splitext(self.destfile)
        with open(fname + '.log', 'a') as file:
            file.write(f'番組開始時刻変更 {self.start_at} -> {start_at} {self.destfile}\n')
        g94.del_rec_task(self.id)
        program = g06.update_program(program)       # 番組情報更新
        g94.rec_task_create(program)                # 録画タスク作成
# --------------------------------------------------
