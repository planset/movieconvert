======
README
======

avconvを使って動画をmp4に変換します。

変換はサーバー側で行い、クライアントはファイルのアップロードとダウンロードを行います。


server
=======
::

    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt
    mkdir data
    python app.py


TASK
=====
* downloadのとき、attachement filenameを返すようにしたほうがいいかも？・・・とおもったがクライアントでファイル名処理したほうが変にならないかも。

