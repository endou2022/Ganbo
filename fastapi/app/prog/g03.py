# ---------------------------------------------------------------------------
# 「予約一覧」ルーチン
# ---------------------------------------------------------------------------
from jinja2 import Environment, FileSystemLoader
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from prog import g92, config

env_j2 = Environment(loader=FileSystemLoader('./templates'), autoescape=True)

router = APIRouter(tags=['予約一覧'])
# --------------------------------------------------


@router.get('/reserved_list')
@router.post('/reserved_list')
def reserved_list():
    '''予約一覧を出力する
    - return : 予約一覧(HTML)
    '''
    # nav_menuのパラメータを整える
    page_title = config.__soft_name__ + " 予約一覧"
    btn_menu = ["", "", "", "cliked", "", "", ""]        # ナビメニューのボタンに色をつける

    search_data = {}
    search_data['service_type'] = 'NO'      # NOの場合は指定なし
    search_data['service_id'] = '0'         # 0の場合は指定なし
    search_data['genre'] = '99'             # 99の場合は指定なし
    key_word = "`予約` is not NULL"
    program_list = g92.search_programs(key_word, search_data)

    # テンプレートに入れる
    # <head> 作成
    add_css = '<link rel="stylesheet" href="/static/css/g03.css">'
    template = env_j2.get_template('html91.j2')
    head = template.render(software=config.software, page_title=page_title, add_css=add_css)

    # <header>作成
    template = env_j2.get_template('html92.j2')
    header = template.render(page_title=page_title, btn_menu=btn_menu)

    # <main>作成
    template = env_j2.get_template('html03.j2')
    main = template.render(program_list=program_list)

    # <footer>作成
    template = env_j2.get_template('html93.j2')
    footer = template.render(footer_str=config.footer_str)

    # データを返す
    return HTMLResponse(content=head + header + main + footer)
# --------------------------------------------------
