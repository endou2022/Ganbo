# -*- coding: utf-8 -*-

#---------------------------------------------------------------------------
# RecTask Class  スレッドを使って録画を管理するクラス
#---------------------------------------------------------------------------
# 汎用のクラスにはしていない＝パラメータチェックなし、エラー処理なし
# concurrent.futures.ThreadPoolExecutor が threading.Thread の上位互換というが、
# メインスレッドを停止したときに、サブスレッドが停止してくれないので、今回は利用しなかった
#---------------------------------------------------------------------------
import threading
import sched		# 組み込みモジュールのイベントスケジューラ。指定時刻にタスクを起動する
import subprocess
import time
import datetime
import logging
from prog import g94
#---------------------------------------------------------------------------
class RecTask():
	'''スレッドを使って録画を管理するクラス'''
	def __init__(self , p_id:int , start_at:datetime , args:tuple):
		'''コンストラクタ
			オブジェクト作成と同時にタスクを登録し、スケジューラを起動する。登録するタスクは１つのみで使う
		- p_id : 番組ID
		- start_at : タスク実行時刻。実行時刻の検査は呼び出し側で行う
		- args rivarun へ渡すパラメータ (host , port , sid , type_ch , rectime , destfile)
		'''
		self.scheduler  = sched.scheduler(time.time, time.sleep)
		self.thread     = threading.Thread(target=self.scheduler.run , daemon=True)		# daemon=Trueにすることで、メインスレッド終了時にサブスレッドも終了する
		self.proc       = None
		self.returncode = None
		self.id         = p_id			# int
		self.start_at   = start_at		# datetime
		self.host       = args[0]		# str
		self.port       = args[1]		# str
		self.sid        = args[2]		# int
		self.type_ch    = args[3]		# str
		self.rectime    = args[4]		# int
		self.destfile   = args[5]		# str
		self.start_str  = start_at.strftime('%Y-%m-%d %H:%M:%S')

		self.set_task()		# タスク登録
		self.thread.start()
# -------------------------
	def set_task(self):
		'''タスクを登録する。scheduler に登録するタスクは１つのみ'''
		self.scheduler.enterabs(self.start_at.timestamp(), 1 , self.run_rivarun) #run_rivarun , debug_task
		# logging.info(f'entry : {self.id} , {self.start_str} , {self.rectime} , {self.destfile}')
		g94.set_recording_status(self.id , '録画予約')
# -------------------------
	def cancel_task(self):
		'''実行前のタスクをすべてキャンセルする。

		scheduler.run() で実行してしまったタスクは操作できない
		'''
		for event in self.scheduler.queue:	# タスクは1つしか登録しないので、こんなことはしなくてよいが
			self.scheduler.cancel(event)
			now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			# logging.info(f'cancel : {self.id} , {now_str} , {self.destfile}')
			g94.set_recording_status(self.id , '予約解除')
# -------------------------
	def stop_task(self):
		'''タスクを止める。

		タスクが実行前ならば、タスクキャンセル、サブプロセスが動いているのならば、サブプロセス停止
		'''
		self.cancel_task()
		if self.proc is not None:
			if self.proc.poll() is None:	# サブプロセスが動いているのならば、サブプロセス停止
				self.proc.kill()
				self.returncode = self.proc.poll()
				now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				logging.info(f'kill : {self.id} , {now_str} , {self.destfile} , returncode = {self.returncode}')
				g94.set_recording_status(self.id , '録画中断')
			else:
				self.returncode = self.proc.poll()
				# logging.info(f'already stop : {self.id} , {self.destfile} , returncode = {self.returncode}')
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
			now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			logging.info(f'start : {self.id} , {now_str} , {self.destfile}')
			g94.set_recording_status(self.id , '録画中')
			# logging.info(f'rivarun --b25 --mirakurun {self.host}:{self.port} --sid {str(self.sid)} --ch {str(self.type_ch)} {str(self.rectime)} {str(self.destfile)}')
			self.proc = subprocess.Popen(['rivarun' , '--b25' , '--mirakurun' , f'{self.host}:{self.port}' , '--sid' , str(self.sid) , '--ch' , str(self.type_ch) , str(self.rectime) , str(self.destfile)])	# すべて文字列で与える必要がある
			self.proc.wait()		# スレッド内で動いてるので、wait() してもメインプロセスは止まらない
			self.returncode = self.proc.poll()
			if self.returncode == 0:	# 0以外は中断されたと思われる
				now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				logging.info(f'finish : {self.id} , {now_str} , {self.destfile} , returncode = {self.returncode}')
				g94.set_recording_status(self.id , '録画完了')
				g94.del_rec_task(self.id)
		except Exception as e:
			# self.proc はNone のままなので、task_is_running() で検査すると '削除済' が返る
			logging.error(f'exception : {self.id} , {now_str} , {self.destfile} , exception = {str(e)}')
			g94.set_recording_status(self.id , str(e))
			g94.del_rec_task(self.id)
# -------------------------
	def debug_task(self , count='30' , id_str='TEST'):
		'''デバッグ用タスク'''
		try:
			now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			logging.info(f'start debug_task : {self.id} , {now_str} , {self.destfile}')
			g94.set_recording_status(self.id , '録画中')
			self.proc = subprocess.Popen(['python', '/app/prog/dummy.py' , str(count) , str(id_str)])
			self.proc.wait()
			self.returncode = self.proc.poll()
			if self.returncode == 0:
				now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
				logging.info(f'finish debug_task : {self.id} , {now_str} , {self.destfile} , returncode = {self.returncode}')
				g94.set_recording_status(self.id , '録画完了')
				g94.del_rec_task(self.id)
		except Exception as e:
			logging.error(f'exception debug_task : {self.id} , {now_str} , {self.destfile} , exception = {str(e)}')
			g94.set_recording_status(self.id , str(e))
			g94.del_rec_task(self.id)
# --------------------------------------------------
