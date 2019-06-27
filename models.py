import os
from sqla_wrapper import SQLAlchemy

db = SQLAlchemy(os.getenv("DATABASE_URL", "sqlite:///localhost.sqlite"))  # this connects to a database either on Heroku or on localhost


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)  # a username must be unique! Two users cannot have the same username
    email = db.Column(db.String)  # email must be unique! Two users cannot have the same email address
    secret_number = db.Column(db.Integer)  # must NOT be unique across user objects
    password = db.Column(db.String)
    session_token = db.Column(db.String)
    intentos = db.Column(db.Integer)
    fecha = db.Column(db.String)
