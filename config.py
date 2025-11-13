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