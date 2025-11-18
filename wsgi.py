from dotenv import load_dotenv

load_dotenv() 
import os
from app import create_app, db

app = create_app()
