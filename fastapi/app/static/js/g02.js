//---------------------------------------------------------------------------
//Ganbo JavaScript
//---------------------------------------------------------------------------
$(function () {
	//終了・新番組
	$('#service_type_ajax').on('change', SearchNewFinal)	//すでにChangeServiceTypeAjaxは紐付けられている
	$('#service_id_ajax').on('change', SearchNewFinal)
	$('#genre_ajax').on('change', SearchNewFinal)
	$('#time_zone_ajax').on('change', SearchNewFinal)
	SearchNewFinal()										//フォームが読み込まれたときに呼び出す
})
//---------------------------------------------------------------------------
/**
 * 終了・新番組表示
 */
function SearchNewFinal() {
	var search_data = JSON.stringify({
		keyword: "",
		service_type: $('#service_type_ajax').val(),
		service_id: $('#service_id_ajax').val(),
		genre: $('#genre_ajax').val(),
		time_zone: $('#time_zone_ajax').val()
	})

	$.post({
		url: '/new_final',
		data: search_data,
		contentType: "application/json"
	})
		.done(function (data, textStatus, jqXHR) {
			$('#search_result').html(data)
			$('#search_result').html(ReplaceARIB)
		})
		.fail(function (jqXHR, textStatus, errorThrown) {
			console.error("通信エラーの内容(new_final) : ", jqXHR.status, jqXHR.statusText, errorThrown)
			alert("通信エラーが発生しました(終了・新番組表示)")
		})
}
//---------------------------------------------------------------------------
