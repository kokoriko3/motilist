from dotenv import load_dotenv

load_dotenv() 
import os
from app import create_app, db
from app.models.user import User
from app.models.plan import Plan,TransportSnapshot,LodgingSnapshot,Itinerary,ItinerarySlot,Template,ShareLink
from app.models.checklist import Checklist,ChecklistItem,Item,Category

app = create_app()
