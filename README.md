# 使用術一覧

<img src="https://img.shields.io/badge/Python-black?logo=python&logoColor=#3776AB">
<img src="https://img.shields.io/badge/FLASK-grey?logo=flask&logoColor=#3BABC3">

## 目次
1.プロジェクト概要  
2.環境  
3.ディレクトリ構造  
4.環境構築  

# プロジェクト概要

## アプリ名
もちリスト

## アプリ概要

目的地、日数を入力するだけで、「旅行プラン(時間と訪れる場所、交通手段、宿泊先)」を提案します。  
生成されたものを自由に編集・カスタマイズ・することき、旅行の計画建てをサポートします。  
また、作られた旅行プランは保存・共有することができ、過去のプランの確認や人のプランの確認ができます。  

# 環境
|言語・フレームワーク|バージョン|
|---|---|
|Python|3.12|
|FLASK|3.0.3|
|PosgreSQL|16|


# ディレクトリ構造

C:.
|   .dockerignore  
|   .env  
|   .gitignore  
|   Caddyfile  
|   config.py  
|   docker-compose.prod.yml  
|   docker-compose.yml  
|   Dockerfile  
|   Dockerfile.dev  
|   manage_data.py  
|   README.md  
|   requirements.txt  
|   seed.py  
|   seed_data.json  
|   tree.txt  
|   wsgi.py  
|     
+---app  
|   |   extensions.py  
|   |   __init__.py  
|   |     
|   +---forms  
|   |   |   auth_form.py  
|   |   |   plan_form.py  
|   |   |   register_form.py  
|   |   |   __init__.py  
|   |   |     
|   |   \---__pycache__  
|   |           plan_form.cpython-313.pyc  
|   |           __init__.cpython-313.pyc  
|   |             
|   +---models  
|   |   |   checklist.py  
|   |   |   plan.py  
|   |   |   user.py  
|   |   |   __init__.py  
|   |   |     
|   |   \---__pycache__  
|   |           checklist.cpython-313.pyc  
|   |           plan.cpython-313.pyc  
|   |           user.cpython-313.pyc  
|   |           __init__.cpython-313.pyc  
|   |             
|   +---routes  
|   |   |   auth_routes.py  
|   |   |   plan_routes.py  
|   |   |   root_routes.py  
|   |   |     
|   |   \---__pycache__  
|   |           plan_routes.cpython-313.pyc  
|   |           root_routes.cpython-313.pyc  
|   |             
|   +---services  
|   |   |   ai_service.py  
|   |   |   db_service.py  
|   |   |   hotel_service.py  
|   |   |   __init__.py  
|   |   |     
|   |   \---__pycache__  
|   |           ai_service.cpython-313.pyc  
|   |           db_service.cpython-313.pyc  
|   |           hotel_service.cpython-313.pyc  
|   |           __init__.cpython-313.pyc  
|   |             
|   +---sql  
|   |       user_table.sql  
|   |         
|   +---static  
|   |   +---css  
|   |   |       style.css  
|   |   |         
|   |   +---img  
|   |   |       logo.png  
|   |   |       rakuten_logo.svg  
|   |   |         
|   |   \---js  
|   |           checklist.js  
|   |           checklist_toggle.js  
|   |           main.js  
|   |           plan_detail.js  
|   |           plan_save.js  
|   |           plan_share.js  
|   |           schedule.js  
|   |           stay.js   
|   |           transport.js  
|   |             
|   +---templates  
|   |   |   layout.html  
|   |   |     
|   |   +---account  
|   |   |       account.html  
|   |   |         
|   |   +---auth  
|   |   |       auth_base.html  
|   |   |       login.html  
|   |   |       register.html  
|   |   |       register_complete.html  
|   |   |         
|   |   +---components  
|   |   |       _plan_card.html  
|   |   |         
|   |   \---plan  
|   |           checklist_create.html  
|   |           checklist_edit.html  
|   |           checklist_list.html  
|   |           detail.html  
|   |           guest_required.html  
|   |           hotel_confirm.html  
|   |           hotel_select.html  
|   |           item_list.html  
|   |           list.html  
|   |           modals.html  
|   |           plan_create.html  
|   |           plan_edit.html  
|   |           public_list.html  
|   |           schedule.html  
|   |           schedule_create.html  
|   |           schedule_edit.html  
|   |           schedule_list.html   
|   |           share_view.html  
|   |           transit.html  
|   |           transport_confirm.html  
|   |           _load.html  
|   |           _plan_header_tabs.html  
|   |           _share_modal.html  
|   |             
|             
\---migrations  
    |   alembic.ini  
    |   env.py  
    |   README   
    |   script.py.mako  
    |     
    \---versions    
            9249e0cf39c7_initial.py     
            eb09e9dc500e_add_template_save_fields.py  
           

# 環境構築

## 開発環境
.env ファイルを以下の環境変数例を元に作成

POSTGRES_USER=app  
POSTGRES_PASSWORD=pass  
POSTGRES_DB=appdb  

config.pyファイルを以下の例をもとに作成

from pathlib import Path
import os

basedir = Path(__file__).resolve().parent.parent

class Config:
    #セキュリティー
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-for-development'

    # --- PostgreSQL 接続設定 ---
    # "L" を追加
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        "postgresql+psycopg://postgres:password@localhost:5432/motilist_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GEMINI_API_KEY = google ai studio からapiキーを取得し入力

    RAKUTEN_APP_ID = 楽天webサービスからapiキーを取得し入力

.envファイルとconfig.pyファイルを作成後、以下のコマンドから開発環境を構築

docker-compose run --rm web flask db upgrade
docker compose up build

#### 動作確認
http://localhost:8000 にアクセスできるか確認
アクセスできアカウントの新規登録が完了すれば成功

### コンテナの停止
以下のコマンドで停止できます

docker compose down -v

## 本番環境
ここではAWS環境での実行方法のみ記述する

EC2でのAmazon LInuxでインスタンスを作成する

sshでアクセスし、以下のコマンドを入力しDocker をインストールする

>dockerのインストール　　
sudo apt-get install -y docker.io docker-compose-plugin

>dockerコマンドをsudoなしで打てるようにする（一度ログアウトが必要）　　
sudo usermod -aG docker $USER

Elastic ipでアドレスを固定しアドレスをメモしておく。

開発環境と同じく.envとconfig.pyを作成する.
その後、以下のコマンドから本番環境を構築

docker-compose run --rm web flask db upgrade　　
docker compose -f docker-compose.pord.yml up build

#### 動作確認
http://ElasticIPで固定したアドレス.nip.io にアクセスできるか確認
アクセスできアカウントの新規登録が完了すれば成功

### コンテナの停止
以下のコマンドで停止できます
docker compose down --remove-orphans

### 環境変数の一覧

|      変数名      |                  役割                  | デフォルト値 |
| :---------------: | :-------------------------------------: | :----------: |
|   POSTGRES_USER   |    posgreSQLのユーザ名(DOcker)で使用    |     app     |
| POSTGRES_PASSWORD |   posgreSQLのパスワード(Docker)で使用   |     pass     |
|    POSTGRES_DB    | posgreSQLのデータベース名(Docker)で使用 |    appdb    |
|PYTHONUNBUUFFERED|Pythonの出力バッファリングを無効か|1|

###  コマンド一覧
|コマンド|実行する処理|
|---|---|
|docker-compose run --rm web flask db upgrade|データベースの更新(初回起動時に実行)|
|docker compose up build |テスト環境で実行|
|docer down -v | テスト環境のダウン|
|docker compose -f docker-compose.pord.yml up build|本番環境で実行|
|docker compose down --remove-orphans|本番環境でのサーバーの停止|
|docker-compose exec web python seed.py|テストデータを投入|
|docker-compose run --rm web python manage_data.py dump|現在のDB情報をjsonにまとめる|

