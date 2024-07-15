## pythonを使ったときに感じたこと

1. 関数の引数が値渡しなのか参照渡しなのか、わかりづらい。<br>
特にクラスオブジェクトを渡す場合、関数内で引数を変更するときに困る。<br>
代入した場合、メモリー（オブジェクト）を共有しているのかどうかわからない。<br>
<-  参照渡しだが、インタプリタで実装されているために、代入するときに新しいメモリ領域が割り当てられる?
1. メモリー管理を行わなくて良いので使いやすい。<br>
関数内でオブジェクトを作って返した場合、オブジェクトがいつまで残っているか不安。<br>
<-  pythonのランタイムで、オブジェクトの参照回数が0になったときに消してくれると言うが……
1. デストラクタがいつ動くのかわからない。<br>
デストラクタで処理したいことがあるが、いつ発動するかわからないので使うことができない。<br>
メモリー管理をしなくても良いというメリットがあるが、オブジェクトがいつまで残っているか不安。<br>
<- del  を使えば良いのだが……
1. オブジェクトにメンバー関数、変数（インスタンス関数、変数）をいつでも追加できる。<br>
使用する関数や変数は、使う前に定義するという流儀に慣れていると気持ち悪い。<br>
無計画にインスタンスを追加すると収拾がつかなくなる。<br>
どこででも定義できるので、どのようなインスタンスを使っているかわからなくなる。<br>
1. クラスの定義は１つのファイルにまとめなければならない。<br>
別のファイルにメンバー関数を書くことができないので、１つのファイルが大きくなる。<br>
1. 関数のオーバーロードができない。<br>
インタプリタだから仕方がないのかもしれないが不便。<br>
ライブラリを使えばできるが、言語仕様として欲しい。<br>
1. クラスのキャストができない。<br>
インタプリタだから仕方がないのかもしれない。<br>
1. スコープが変。<br>
他のファイルにある関数や変数は、importしたファイル名をつけて参照する必要がある。<br>
グローバル変数は、定義したファイル内でのみ有効。<br>
他のファイルでは、定義ファイル名.変数名  で参照する必要がある。<br>
クラスの内部からインスタンス変数（関数）を参照する場合に、self  をつける必要がある。クラス内で呼び出す場合はそのままの名前で呼び出したい
1. インタプリタだから実行時にしか文法エラーがわからない。<br>
別にかまわないけれども、import文のエラーくらいは先に見つけてほしい。<br>
1. pythonの実装言語はC言語?<br>
別にかまわないけれども、pythonで実装されていない。
1. 公開されているライブラリが豊富<br>
ソフトを作るのには、言語仕様よりも、ライブラリの数と質!。<br>
Delphi , C++Builder  も見習って欲しい。