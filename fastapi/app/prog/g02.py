# ---------------------------------------------------------------------------
# 「終了・新番組」ルーチン
# ---------------------------------------------------------------------------
from jinja2 import Environment, FileSystemLoader
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from prog import g92, config

env_j2 = Environment(loader=FileSystemLoader('./templates'), autoescape=True)

router = APIRouter(tags=['終了・新番組'])
# --------------------------------------------------


@router.get('/new-final-list')
@router.post('/new-final-list')
def get_programs_new_final_list():
    '''終了・新番組画面を出力する
    - return : 終了・新番組画面(HTML)
    '''
    # nav_menuのパラメータを整える
    page_title = config.__soft_name__ + " 終了・新番組"
    btn_menu = ["", "", "cliked", "", "", "", ""]        # ナビメニューのボタンに色をつける

    # テンプレートに入れる
    # <head> 作成
    add_js = '<script src="/static/js/g02.js"></script>'
    add_css = '<link rel="stylesheet" href="/static/css/g02.css">'
    template = env_j2.get_template('html91.j2')
    head = template.render(software=config.software, page_title=page_title, add_css=add_css, add_js=add_js)

    # <header>作成
    template = env_j2.get_template('html92.j2')
    header = template.render(page_title=page_title, btn_menu=btn_menu)

    # <main>作成
    template = env_j2.get_template('html02.j2')
    main = template.render()

    # <footer>作成
    template = env_j2.get_template('html93.j2')
    footer = template.render(footer_str=config.footer_str)

    # データを返す
    return HTMLResponse(content=head + header + main + footer)
# --------------------------------------------------


@router.post('/new_final')
def get_programs_new_final(search_data: dict):
    '''終了・新番組を検索して出力する。
    番組名の 🈟,🈠,🈡 を検索して出力する
    - search_data 検索条件、search_data はすべて文字列で来る
    - return : 終了・新番組(HTML)
    '''
    # 新番組 🈟,🈠
    key_word = "(`番組名` LIKE '%🈟%') OR (`番組名` LIKE '%🈠%')"        # LIKE と IN の同時使用は不可
    new_program_list = g92.search_programs(key_word, search_data)

    # 終了番組 🈡
    key_word = "`番組名` LIKE '%🈡%'"
    final_program_list = g92.search_programs(key_word, search_data)

    # 終了・新番組表出力
    template = env_j2.get_template('html12.j2')
    main = template.render(new_program_list=new_program_list, final_program_list=final_program_list)
    return HTMLResponse(content=main)
# --------------------------------------------------
