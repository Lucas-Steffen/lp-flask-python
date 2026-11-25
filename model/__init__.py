from app import app
from model.user import *
from model.product import *
from model.movement import *


with app.app_context():
    db.create_all()
