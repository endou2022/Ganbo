//---------------------------------------------------------------------------
//Ganbo JavaScript
//---------------------------------------------------------------------------
$(function () {
    //番組検索
    $('#search_prog').on('click', SearchProg);            //番組検索
    $('#service_type_ajax').on('change', SearchProg);
    $('#service_id_ajax').on('change', SearchProg);
    $('#genre_static').on('change', SearchProg);
    $('#open_keyword_dialog').on('click', OpenKWDlog);   //登録ダイアローグを開く
    $('#set_keyword_dialog').on('close', SetKeyword);    //自動予約設定登録
})
//---------------------------------------------------------------------------
/**
 * 番組検索
 */
function SearchProg() {
    // https://atmarkit.itmedia.co.jp/ait/articles/1702/10/news033.html (2024/01/25)
    // https://qiita.com/pappikko/items/117efc8bcf5e9c3be9e1 (2023/12/27)
    if (!$('#search_form')[0].reportValidity()) {    // フォームを検証する
        return;
    }
    // https://fumidzuki.com/knowledge/4122/ (2024/01/24)
    // https://js.studio-kingdom.com/jquery/ajax/ajax (2024/01/24)
    var search_data = JSON.stringify({    // formの内容をjson形式でセットする
        key_word: $('#keyword').val(),
        service_type: $('#service_type_ajax').val(),
        service_id: $('#service_id_ajax').val(),
        genre: $('#genre_static').val(),
    })

    // https://fumidzuki.com/knowledge/4122/ (2024/01/24)
    $.post({
        url: '/search_prog',
        data: search_data,
        contentType: "application/json"        // json形式での送信 ※重要
    })
        .done(function (data, textStatus, jqXHR) {
            $('#search_result').html(data);
            $('#search_result').html(ReplaceARIB);
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
            console.error("通信エラーの内容(search_prog) : ", jqXHR.status, jqXHR.statusText, errorThrown)
            alert("通信エラーが発生しました(番組検索)");
        })
}
//---------------------------------------------------------------------------
/**
 * 自動予約設定登録
 */
function SetKeyword() {
    if (this.returnValue != '自動予約登録') {
        return;
    }

    if (!$('#search_form')[0].reportValidity()) {
        return;
    }

    //自動予約設定の登録、録画予約
    var keyword_data = JSON.stringify({
        key_word: $('#keyword').val(),
        service_type: $('#service_type_ajax').val(),
        service_id: $('#service_id_ajax').val(),
        genre: $('#genre_static').val(),
        margin_before: $('#margin_before').val(),
        margin_after: $('#margin_after').val()
    })

    $.post({
        url: '/set_keyword',
        data: keyword_data,
        contentType: "application/json"
    })
        .done(function (data, textStatus, jqXHR) {
            console.table(data);
            SearchProg();           //検索結果を変更する
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
            console.error("通信エラーの内容(set_keyword) : ", jqXHR.status, jqXHR.statusText, errorThrown)
            alert("通信エラーが発生しました(自動予約設定登録)");
        })
}
//---------------------------------------------------------------------------
/**
 * 自動予約設定ダイアローグを開く
 */
function OpenKWDlog() {
    if (!$('#search_form')[0].reportValidity()) {    // フォームを検証する
        return;
    }

    $('#dlog_keyword').text($('#keyword').val());
    $('#dlog_service_type').text($('#service_type_ajax option:selected').text());
    $('#dlog_service').text($('#service_id_ajax option:selected').text());
    $('#dlog_genre').text($('#genre_static option:selected').text());
    $("#set_keyword_dialog")[0].showModal();
}
//---------------------------------------------------------------------------
