# wsgi.py
from dotenv import load_dotenv

load_dotenv() 
import os
from app import create_app
# dbのインポート元を extensions に変更
from app.extensions import db 

from app.models.user import User
from app.models.plan import Plan, TransportSnapshot, StaySnapshot, Schedule, ScheduleDetail, Template, Share
from app.models.checklist import Checklist, ChecklistItem, Item, Category

app = create_app()