//---------------------------------------------------------------------------
//Ganbo JavaScript
//---------------------------------------------------------------------------
$(function () {
    //自動予約一覧
    $('#update_keyword_dialog').on('close', UpdateKeywordDlgClose);
    $('#update_keyword_dialog').on('change', '#service_type_ajax', function () { ChangeServiceTypeAjax() });      //Ajaxで付け加えたエレメントにイベントを付ける
    $('.keyword_edit').on('click', function () { LoadKeyword($(this).closest('tr').attr('id')) });                //キーワードの編集
    $('.reserve_list').on('click', function () { ViewReserved($(this).closest('tr').attr('id')) });               //無効予約も含む予約番組の一覧
});
//---------------------------------------------------------------------------
/**
 * 自動予約設定の情報を呼び出して表示する
 *
 * @param int id 自動予約ID
 */
function LoadKeyword(id) {
    $.get('/load_keyword/' + id)
        .done(function (data, textStatus, jqXHR) {
            $('#update_keyword_dialog').html(data);
            $("#update_keyword_dialog")[0].showModal();            //ダイアローグを開く
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
            console.error("通信エラーの内容(load_keyword) : ", jqXHR.status, jqXHR.statusText, errorThrown)
            alert("通信エラーが発生しました(自動予約設定表示)");
        })
}
//---------------------------------------------------------------------------
/**
 * キーワードダイアローグが閉じられた
 */
function UpdateKeywordDlgClose() {
    id = $('#automatic_id').val();
    switch (this.returnValue) {
        case '削除': DeleteKeyword(id); break;
        case '変更': UpdateKeyword(id); break;
    }
}
//---------------------------------------------------------------------------
/**
 * 自動予約設定を削除する
 *
 * @param int id 自動予約ID
 */
function DeleteKeyword(id) {
    $.get('/delete_keyword/' + id)
        .done(function (data, textStatus, jqXHR) {
            console.table(data);
            $('#' + id).remove();       //当該行のみ削除する
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
            console.error("通信エラーの内容(delete_keyword) : ", jqXHR.status, jqXHR.statusText, errorThrown);
            alert("通信エラーが発生しました(自動予約設定削除)");
        })
}
//---------------------------------------------------------------------------
/**
 * 自動予約設定を更新する
 */
function UpdateKeyword() {
    if (!$('#automatic_form')[0].reportValidity()) {
        return;
    }

    var update_data = JSON.stringify({
        automatic_id: $('#automatic_id').val(),
        key_word: $('#dlog_keyword').val(),
        service_type: $('#service_type_ajax').val(),
        service_id: $('#service_id_ajax').val(),
        genre: $('#genre_static').val(),
        margin_before: $('#margin_before').val(),
        margin_after: $('#margin_after').val(),
    })

    $.post({
        url: '/update_keyword',
        data: update_data,
        contentType: "application/json"
    })
        .done(function (data, textStatus, jqXHR) {
            $('.button-036.cliked').click();    //「自動予約一覧」がクリックしてある
            console.table(data);
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
            console.error("通信エラーの内容(update_keyword) : ", jqXHR.status, jqXHR.statusText, errorThrown);
            alert("通信エラーが発生しました(自動予約情報更新)");
        })
}
//---------------------------------------------------------------------------
/**
 * 無効予約を含む予約一覧を表示する
 *
 * @param int id 自動予約ID
 */
function ViewReserved(id) {
    $.get('/view_reserved/' + id)
        .done(function (data, textStatus, jqXHR) {
            $('#view_reserved_dialog').html(data);
            $('#view_reserved_dialog').html(ReplaceARIB);
            $("#view_reserved_dialog")[0].showModal();
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
            console.error("通信エラーの内容(view_reserved) : ", jqXHR.status, jqXHR.statusText, errorThrown);
            alert("通信エラーが発生しました(予約一覧表示)");
        })
}
//---------------------------------------------------------------------------
