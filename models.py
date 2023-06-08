# models.py

from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    register = db.Column(db.String(20), unique=True)
    association = db.Column(db.String(100))
    function = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    key = db.Column(db.String(1000))
    timestamp = db.Column(db.DateTime)

