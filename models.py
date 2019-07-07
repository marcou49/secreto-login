import os
import datetime
from sqla_wrapper import SQLAlchemy

db = SQLAlchemy(os.getenv("DATABASE_URL", "sqlite:///localhost.sqlite"))  # this connects to a database either on Heroku or on localhost


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)  # a username must be unique! Two users cannot have the same username
    email = db.Column(db.String)  # email must be unique! Two users cannot have the same email address
    password = db.Column(db.String)
    residencia = db.Column(db.String)
    session_token = db.Column(db.String)
    deleted = db.Column(db.Boolean, default=False)


class Mensaje(db.Model):
    __tablename__ = "mensaje"

    id = db.Column(db.Integer, primary_key=True)
    asunto = db.Column(db.String)
    texto = db.Column(db.Text)
    destinatario = db.Column(db.String, db.ForeignKey("user.email"))
    sender = db.Column(db.String, db.ForeignKey("user.email"))
    leido = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.datetime.now)






