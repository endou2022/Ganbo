//---------------------------------------------------------------------------
//Ganbo JavaScript
//---------------------------------------------------------------------------
/**
 * ARIB外字（アライブがいじ）の定義
 * https://ja.wikipedia.org/wiki/ARIB%E5%A4%96%E5%AD%97 (2024/01/21)
 * https://ja.wikipedia.org/wiki/%E7%95%AA%E7%B5%84%E8%A1%A8#%E8%A8%98%E5%8F%B7 (2024/01/21)
 */
regexp_string = /🅊|🅌|🄿|🅆|🅋|🈐|🈑|🈒|🈓|🅂|🈔|🈕|🈖|🅍|🄱|🄽|🈗|🈘|🈙|🈚|🈛|⚿|🈜|🈝|🈞|🈟|🈠|🈡|🈢|🈣|🈤|🈥|🅎|㊙|🈀/g
stringMap = {
	'🅊': '',
	'🅌': '',
	'🄿': '',
	'🅆': '',
	'🅋': '',
	'🈐': '[手]',
	'🈑': '[字]',
	'🈒': '',
	'🈓': '[デ]',
	'🅂': '',
	'🈔': '[二]',
	'🈕': '[多]',
	'🈖': '[解]',
	'🅍': '',
	'🄱': '',
	'🄽': '',
	'🈗': '',
	'🈘': '',
	'🈙': '<span class="arib_gaiji">映</span>',
	'🈚': '<span class="arib_gaiji">無料</span>',
	'🈛': '',
	'⚿': '',
	'🈜': '[前編]',
	'🈝': '[後編]',
	'🈞': '[再]',
	'🈟': '<span class="arib_gaiji">新</span>',
	'🈠': '<span class="arib_gaiji">初</span>',
	'🈡': '<span class="arib_gaiji">終</span>',
	'🈢': '[生]',
	'🈣': '',
	'🈤': '',
	'🈥': '<span class="arib_gaiji">吹</span>',
	'🅎': '',
	'㊙': '(秘)',
	'🈀': 'ほか'
}
//---------------------------------------------------------------------------
/**
 * ページが読み込まれた後の処理
 */
$(function () {
	$.ajaxSetup({
		async: false, 						//同期通信にする Ajaxの返事を待って処理するために同期通信にしておく
		cache: false						//キャッシュを無効にする
	});

	$('main').html(ReplaceARIB);			//番組表で使われるARIB外字を変換する

	//ナビゲーションメニューの処理
	$("input[name='service_type']").on('change', NavMenuSubmit);
	$('#service_id').on('change', NavMenuSubmit);
	$('#genre').on('change', NavMenuSubmit);
	$("input[name='nav_day']").on('change', NavMenuSubmit);
	$("input[name='nav_time']").on('change', NavMenuSubmit);

	//詳細表示
	$('.content-area').on('click', function () { GetDetail($(this).attr('id')) });					//番組表をクリックしたら詳細ダイアローグを出す
	$('.one_program').on('click', function () { GetDetail($(this).attr('id')) });					//週間番組表の番組詳細
	// Ajaxで付け加えたエレメントもイベントを付ける手法
	// https://qiita.com/mako0104/items/9548e015fa279308c5ab (2024/02/01)
	// https://www.sejuku.net/blog/38774#index_id8 (2024/02/01)
	$('#search_result').on('click', '.program_name', function () { GetDetail($(this).closest('tr').attr('id')) });			//一覧表示や検索リストの番組詳細
	$('#search_result').on('click', '.toggle_reserve', function () { ToggleReserve($(this).closest('tr').attr('id')) });	//一覧表示や検索結果の予約反転

	$('#service_type_ajax').on('change', ChangeServiceTypeAjax);
	$("#detail").on('close', DetailClosed);																//番組詳細ダイアローグが閉じられたらフォームを送信する
});
//---------------------------------------------------------------------------
/**
 * 番組表で使われるARIB外字を変換する
 *
 * @param int index : 何番目の項目か
 * @param string element : 置換対象文字列
 * @param regexp_string : 置換対象文字 (g00.jsの先頭で定義)
 * @param stringMap 置換文字 (g00.jsの先頭で定義)
 * @returns 置換後の文字列
 * @link https://www.javadrive.jp/javascript/regexp/index8.html#section3 (2024/01/21)
 * @link https://lallapallooza.jp/4603/#i-17 (2024/01/21)
 */
function ReplaceARIB(index, element) {
	return element.replace(regexp_string, function (match_str) {
		return stringMap[match_str]
	})
}
//---------------------------------------------------------------------------
/**
 * 番組情報の詳細表示->「その他の情報」の中にある `&lt;br&gt;` を `<br>` タグに戻す
 * Jinja2が `<br>` までエスケープするので、本体がロードされた後にJavaScriptで変える必要がある
 *
 * @param int index : 何番目の項目か
 * @param string element : 置換対象文字列
 * @returns 置換後の文字列
 */
function ReplaceBR(index, element) {
	return element.replace(/&lt;br&gt;/g, '<br>')
}
//---------------------------------------------------------------------------
/**
 * ナビゲーションメニューのサービス、日時が変更された
 * click クラスの付いているボタンをソフトウエア的にクリックして Form を送信し画面遷移する
 */
function NavMenuSubmit() {
	$('.button-036.cliked').click();	//クラス名の間にスペースを入れてはいけない
}
//---------------------------------------------------------------------------
/**
 * 番組の詳細をダイアローグで表示する
 *
 * @param int id 番組ID
 */
function GetDetail(id) {
	$.get('/get_detail/' + id)
		.done(function (data, textStatus, jqXHR) {
			// http://karashidaimyojin.com/jquery/ajax-post/ (2024/01/04)
			$('#detail').html(data)
			$('#detail_prog_name').html(ReplaceARIB)
			$('#detail_exp').html(ReplaceARIB)
			$('#detail_ext').html(ReplaceARIB)
			//<br>までJinja2でエスケープされてしまうので元に戻す
			$('#detail_ext').html(ReplaceBR)
			// https://rukiadia.hatenablog.jp/entry/2014/06/18/131504 (2023/12/17)
			$("#detail")[0].showModal();
		})
		.fail(function (jqXHR, textStatus, errorThrown) {
			// https://developer.mozilla.org/ja/docs/Web/API/console (2024/01/25)
			// https://qiita.com/kenjiuno/items/5d7df3b3acc39a4df426 (2024/01/25)
			console.error("通信エラーの内容(get_detail) : ", jqXHR.status, jqXHR.statusText, errorThrown)
			alert("通信エラーが発生しました(詳細ダイアローグ表示)")
		})
}
//---------------------------------------------------------------------------
/**
 * 予約状況を反転させる
 *
 * @param int id 番組ID
 */
function ToggleReserve(id) {
	$.get('/toggle_reserve/' + id)
		.done(function (data, textStatus, jqXHR) {
			if (data.can_not_change) {		//終了した番組、録画中の番組を操作しようとした
				return
			}
			//予約状況の表示操作
			if (data.reserve_str == null) {
				$('#' + id + '>.toggle_reserve').text('-')
			} else {
				$('#' + id + '>.toggle_reserve').text(data.reserve_str)
			}
			//予約状況に応じて透過度を設定
			switch (data.reserve_str) {
				case '○':
					$('#' + id).removeClass('not_reserved')
					break;
				case '×':
					$('#' + id).addClass('not_reserved')
					break;
				case null:
					$('#' + id).addClass('not_reserved')
					break;
			}
		})
		.fail(function (jqXHR, textStatus, errorThrown) {
			console.error("通信エラーの内容(toggle_reserve) : ", jqXHR.status, jqXHR.statusText, errorThrown)
			alert("通信エラーが発生しました(予約状況反転)")
		})
}
//---------------------------------------------------------------------------
/**
 * 番組詳細ダイアローグが閉じられたらフォームを送信する
 */
function DetailClosed() {
	// this.returnValue が押したボタンの valueの値
	// https://developer.hatenastaff.com/entry/2021/12/01/100000 (2023/12/21)
	id = $('#program_id').val()
	switch (this.returnValue) {
		case '録画中止': StopRecording(id); SetReserve(id, null); break;
		case '録画開始': SetReserve(id, '○'); break;
		case '予約変更': SetReserve(id, '○'); break;
		case '録画予約': SetReserve(id, '○'); break;
		case '予約有効': SetReserve(id, '○'); break;
		case '予約削除': SetReserve(id, null); break;
		case '予約無効': SetReserve(id, '×'); break;
	}
}
//---------------------------------------------------------------------------
/**
 * 録画中止
 *
 * @param int id 番組ID
 */
function StopRecording(id) {
	$.get('/del_rec_task/' + id)
		.done(function (data, textStatus, jqXHR) {
			console.log(data)
			$('#' + id).removeClass('on_recording')
		})
		.fail(function (jqXHR, textStatus, errorThrown) {
			console.error("通信エラーの内容(del_rec_task) : ", jqXHR.status, jqXHR.statusText, errorThrown)
			alert("通信エラーが発生しました(録画中止)")
		})
}
//---------------------------------------------------------------------------
/**
 * 番組予約を設定する
 *
 * @param int id : 番組ID
 * @param string reserve_str : 予約情報 ('○' | '×' | null)
 */
function SetReserve(id, reserve_str) {
	var reserve_data = JSON.stringify({
		id: id,
		reserve: reserve_str,
		detail_before: $("#detail_form input[name='margin_before']").val(),
		detail_after: $("#detail_form input[name='margin_after']").val(),
		file_name: $("#detail_form input[name='save_file_name']").val()
	})

	f_name = $("#detail_form input[name='save_file_name']").val()

	$.post({
		url: '/set_reserve',
		data: reserve_data,
		contentType: "application/json"
	})
		.done(function (data, textStatus, jqXHR) {
			/* data.is_start = 0|1 が帰ってくる。JavaScript は数値・文字列のどちらでも都合の良い方に解釈してくれる */
			if (data.is_start == '1') {
				if ($('#' + id).hasClass('content-area') || $('#' + id).hasClass('one_program')) {
					$('#' + id).addClass('valid_reserved')
					$('#' + id).removeClass('invalid_reserved')
					$('#' + id).addClass('on_recording')
				}
				$('#' + id + '>.toggle_reserve').text('○')
			} else {
				switch (data.reserve_str) {
					case '○':
						if ($('#' + id).hasClass('content-area') || $('#' + id).hasClass('one_program')) {
							$('#' + id).addClass('valid_reserved')
							$('#' + id).removeClass('invalid_reserved')
						}
						$('#' + id + '>.toggle_reserve').text('○')
						$('#' + id + '>.program_name').text(f_name)
						break;
					case '×':
						if ($('#' + id).hasClass('content-area') || $('#' + id).hasClass('one_program')) {
							$('#' + id).addClass('invalid_reserved')
							$('#' + id).removeClass('valid_reserved')
						}
						$('#' + id + '>.toggle_reserve').text('×')
						break;
					case null:
						if ($('#' + id).hasClass('content-area') || $('#' + id).hasClass('one_program')) {
							$('#' + id).removeClass('invalid_reserved')
							$('#' + id).removeClass('valid_reserved')
						}
						$('#' + id + '>.toggle_reserve').text('-')
						break;
				}
			}
		})
		.fail(function (jqXHR, textStatus, errorThrown) {
			console.error("通信エラーの内容(set_reserve) : ", jqXHR.status, jqXHR.statusText, errorThrown)
			alert("通信エラーが発生しました(番組予約設定)")
		})
}
//---------------------------------------------------------------------------
/**
 * 番組検索画面、自動予約一覧で、サービスタイプが変更になったので、サービス名(ID)を変える
 */
function ChangeServiceTypeAjax() {
	type = $('#service_type_ajax').val()
	$.get('/get_option_service_id/' + type)
		.done(function (data, textStatus, jqXHR) {
			$('#service_id_ajax').html(data)
		})
		.fail(function (jqXHR, textStatus, errorThrown) {
			console.error("通信エラーの内容(get_option_service_id) : ", jqXHR.status, jqXHR.statusText, errorThrown)
			alert("通信エラーが発生しました(サービスタイプ変更)")
		})
}
//---------------------------------------------------------------------------
