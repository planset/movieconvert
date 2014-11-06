======
README
======

* avconvを使って動画をmp4に変換する
* 変換はサーバー側で行う
* クライアント側はファイルのアップロードとダウンロードを行う


server
=======
::

    sudo bash install.sh
    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt
    mkdir data
    python app.py


client
======
1. movie_to_mp4_at_server.pyのHOSTとPORTを設定
2. 実行::

    ./movie_to_mp4_at_server.py INPUT_FILE_NAME


