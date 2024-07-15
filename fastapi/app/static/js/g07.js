//---------------------------------------------------------------------------
//Ganbo JavaScript Setting
//---------------------------------------------------------------------------
$(function () {
	//設定
	$("#test_addr").on('click', TestAddrPort);	//通信テストボタンクリック
	$('#set_addr').on('click', SetAddrPort);	//mirakurunサーバータブ 決定ボタンクリック
	$("#color_setting").on('click', SetColor);	//ジャンル別背景タブ 決定ボタンクリック
	$("#gr_setting").on('click', SetService);	//サービスに関する設定 決定ボタンクリック
	$("#bs_setting").on('click', SetService);
	$("#cs_setting").on('click', SetService);
	$("#std_setting").on('click', SetStd);		//録画標準設定 決定ボタンクリック
	$('#reflesh_programs').on('click', RefleshPrograms);	//番組情報更新
})
//---------------------------------------------------------------------------
/**
 * mirakurunサーバータブ -> 通信テストボタンクリック
 */
function TestAddrPort() {
	if (!$('#set_addr_form')[0].reportValidity()) {
		return;
	}
	ip_addr = $('#ip_addr').val()
	port = $('#port').val()

	$.get('/test_addr_port/' + ip_addr + '/' + port)
		.done(function (data, textStatus, jqXHR) {
			if (data.result) {
				$('#server_result').html(data.html)
			} else {
				console.error("例外の内容 : ", data.exception)
				alert("mirakurun との通信で、エラーが発生しました")
			}
		})
		.fail(function (jqXHR, textStatus, errorThrown) {
			console.error("通信エラーの内容(test_addr_por) : ", jqXHR.status, jqXHR.statusText, errorThrown)
			alert("通信エラーが発生しました(通信テスト)")
		})
}
//---------------------------------------------------------------------------
/**
 * mirakurunサーバータブ -> 決定ボタンクリック
 */
function SetAddrPort() {
	if (!$('#set_addr_form')[0].reportValidity()) {
		return;
	}
	ip_addr = $('#ip_addr').val()
	port = $('#port').val()

	$.post('/set_addr_port/' + ip_addr + '/' + port)
		.done(function (data, textStatus, jqXHR) {
			if (data.result) {
				alert('データを更新しました\nサービス ' + data.channels + ' 件')
				location.reload(true);		// ページ再読み込み
			} else {
				console.error("例外の内容 : ", data.exception)
				alert("mirakurun との通信で、エラーが発生しました")
			}
		}).fail(function (jqXHR, textStatus, errorThrown) {
			console.error("通信エラーの内容(set_addr_port) : ", jqXHR.status, jqXHR.statusText, errorThrown)
			alert("通信エラーが発生しました(アドレス、ポート設定)")
		})
}
//---------------------------------------------------------------------------
/**
 * ジャンル別背景タブ -> 決定ボタンクリック
 */
function SetColor() {
	$.post('/set_color', $('#color_setting_form').serialize())
		.done(function (data, textStatus, jqXHR) {
			alert("データを更新しました")
		}).fail(function (jqXHR, textStatus, errorThrown) {
			console.error("通信エラーの内容(set_color) : ", jqXHR.status, jqXHR.statusText, errorThrown)
			alert("通信エラーが発生しました(背景色設定)")
		})
}
//---------------------------------------------------------------------------
/**
 * サービズタブ -> 決定ボタンクリック
 */
function SetService() {
	form_str = '#' + this.id + '_form'
	$.post('/set_service', $(form_str).serialize())
		.done(function (data, textStatus, jqXHR) {
			alert("データを更新しました")
			location.reload(true);
		}).fail(function (jqXHR, textStatus, errorThrown) {
			console.error("通信エラーの内容(set_service) : ", jqXHR.status, jqXHR.statusText, errorThrown)
			alert("通信エラーが発生しました(サービス設定)")
		})
}
//---------------------------------------------------------------------------
/**
* 録画標準設定タブ -> 決定ボタンクリック
*/
function SetStd() {
	if (!$('#std_setting_form')[0].reportValidity()) {
		return;
	}

	$.post('/set_std', $('#std_setting_form').serialize())
		.done(function (data, textStatus, jqXHR) {
			alert("データを更新しました")
		}).fail(function (jqXHR, textStatus, errorThrown) {
			console.error("通信エラーの内容(set_std) : ", jqXHR.status, jqXHR.statusText, errorThrown)
			alert("通信エラーが発生しました(標準設定)")
		})
}
//---------------------------------------------------------------------------
/**
 * 番組情報更新
 */
function RefleshPrograms() {
	$.get('/reflesh_programs')
		.done(function (data, textStatus, jqXHR) {
			if (data.result) {
				console.table(data)
				alert("番組情報を更新しました。\n番組情報 = " + data.prog_num + " 更新件数 = " + data.chg_prog + " 番組名変更数 = " + data.chg_name)
			} else {
				console.error(data)
				alert("番組情報更新中にエラーが発生しました")
			}
		})
		.fail(function (jqXHR, textStatus, errorThrown) {
			console.error("通信エラーの内容(reflesh_programs) : ", jqXHR.status, jqXHR.statusText, errorThrown)
			alert("通信エラーが発生しました(番組情報更新)")
		})
}
//---------------------------------------------------------------------------