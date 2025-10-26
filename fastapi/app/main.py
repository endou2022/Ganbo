# ---------------------------------------------------------------------------
# メインルーチン
# ---------------------------------------------------------------------------
import locale
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from prog import config, g00, g01, g02, g03, g04, g05, g06, g07, g91, g92, g94, g95


# --------------------------------------------------
class MyHeadersMiddleware(BaseHTTPMiddleware):
    '''任意のヘッダーをレスポンスに追加する

    @link https://qiita.com/sh0nk/items/493214c7626116a49870 (2024/06/18)
    @link https://fastapi.tiangolo.com/tutorial/middleware/#create-a-middleware (2024/06/18)
    @link https://qiita.com/mint__/items/a4039d3cc659959d9231 (2024/06/18)

    Content-Security-Policy の設定もした方が良いかもしれない。
    https://liginc.co.jp/blog/tech/639126 (2024/06/18)
    '''

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # response.headers["Cache-Control"] = "no-cache, no-store"
        # https://www.ipa.go.jp/security/vuln/websecurity/clickjacking.html (2024/06/18)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        # https://qiita.com/KWS_0901/items/c8f0bd39751cc845ea64 (2024/06/18)
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

# --------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    '''起動時、終了時の処理を行う

    app = FastAPI()より上流に書いておく必要がある。
    @link https://fastapi.tiangolo.com/advanced/events/ (2024/03/25)
    '''

    # 起動時に実施すること
    # docker compose up -d としたときに、mariadb が立ち上がるまで5秒待つ。depend_onではうまくいかなかった。sleep(5)でもうまくいっていない。
    time.sleep(5)
    # https://zenn.dev/dencyu/articles/2b58f669bcd473 (2025/01/01)
    # https://qiita.com/shinsa82/items/a0778fbd127012c93577 (2025/01/01)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # strftime('%m月%d日(%a)') で %a を日本語にするために、
    # FastAPIコンテナのローケルをJapanに、時間帯をJSTにしておく必要がある
    # 最初に設定しておけば、個々のファイルで設定する必要はない
    # https://note.nkmk.me/python-datetime-day-locale-function/#_1 (2024/01/07)
    locale.setlocale(locale.LC_TIME, 'ja_JP.UTF-8')

    g07.get_std_from_db()                # グローバル変数の設定
    g94.register_all_reservations()      # 起動時にすべての録画予約を録画タスクに登録する
    g95.start_schedule()                 # 番組情報取得ルーチンを開始する

    logging.info(config.__soft_name__ + " 起動")

    yield
    # 終了時に実施すること
    g94.del_all_rec_task()
    g95.clear_schedule()
    logging.info(config.__soft_name__ + " 停止")
# --------------------------------------------------
# https://fastapi.tiangolo.com/ja/tutorial/metadata/ (2024/05/01)
app = FastAPI(title=config.__soft_name__,
              description=f"<h1>{config.__description__}</h1>",
              version=config.__version__,
              lifespan=lifespan,
              license_info={"name": "BSD License"})

# https://qiita.com/rubberduck/items/3734057d92a5ee7a2e83 (2024/02/01)
app.mount(path="/static", app=StaticFiles(directory="static"), name="static")
app.add_middleware(MyHeadersMiddleware)
app.include_router(g00.router)
app.include_router(g01.router)
app.include_router(g02.router)
app.include_router(g03.router)
app.include_router(g04.router)
app.include_router(g05.router)
app.include_router(g06.router)
app.include_router(g07.router)
app.include_router(g91.router)
app.include_router(g92.router)
app.include_router(g94.router)
# --------------------------------------------------
