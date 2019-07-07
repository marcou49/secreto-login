import hashlib
import random
import uuid
import datetime
import requests
import locale

from flask import Flask, render_template, request, make_response, redirect, url_for
from models import Mensaje, User, db

app = Flask(__name__)
db.create_all()  # create (new) tables in the database


@app.route("/", methods=["GET"])
def index():
    session_token = request.cookies.get("session_token")

    if session_token:
        user = db.query(User).filter_by(session_token=session_token).first()
        query = user.residencia
        unit = "metric"  # use "imperial" for Fahrenheit
        api_key = "7fe12181af58ce5af40a5e82dc3aad91"
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        fecha = datetime.date.today()
        hoy = fecha.strftime('%A %d de %B')

        url = "https://api.openweathermap.org/data/2.5/weather?q={0}&units={1}&appid={2}&lang=es".format(query, unit,
                                                                                                         api_key)
        data = requests.get(url=url)

        mensajes = db.query(Mensaje).filter_by(destinatario=user.email, leido=False).all()

        return render_template("index.html", hoy=hoy, user=user, mensajes=mensajes, data=data.json())

    else:
        user = None

        return render_template("index.html", user=user)


@app.route("/login", methods=["POST"])

def login():

    name = request.form.get("user-name")
    email = request.form.get("user-email")
    password = request.form.get("user-password")
    residencia = request.form.get("residencia")

    # hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # see if user already exists
    user = db.query(User).filter_by(email=email).first()


    if user:

        registro ='registrado'
        return redirect(url_for('index', registro=registro))


    if not user:
        # create a User object
        user = User(name=name, email=email, password=hashed_password, residencia=residencia)

        # save the user object into a database
        db.add(user)
        db.commit()

    if user and user.deleted == 1:

        return "Te diste de baja amigo, date de alta con otro usuario / Contraseña"


    # check if password is incorrect
    if hashed_password != user.password:
        return "WRONG PASSWORD! Go back and try again."

    elif hashed_password == user.password:
        # create a random session token for this user
        session_token = str(uuid.uuid4())

        # save the session token in a database
        user.session_token = session_token
        db.add(user)
        db.commit()

        # save user's session token into a cookie
        response = make_response(redirect(url_for('index')))
        response.set_cookie("session_token", session_token, httponly=True, samesite='Strict')

        return response



@app.route("/ingreso", methods=["POST"])

def ingreso():


    email = request.form.get("user-email")
    password = request.form.get("user-password")

    # hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # see if user already exists
    user = db.query(User).filter_by(email=email).first()


    if not user:

        noregistro ='no-registrado'
        return redirect(url_for('index', noregistro=noregistro))


    if user and user.deleted == 1:

        borrado = 'borrado'
        return redirect(url_for('index', borrado=borrado))


    # check if password is incorrect
    if hashed_password != user.password:

        error = 'error'
        return redirect(url_for('index', error=error))

    elif hashed_password == user.password:
        # create a random session token for this user
        session_token = str(uuid.uuid4())

        # save the session token in a database
        user.session_token = session_token
        db.add(user)
        db.commit()

        # save user's session token into a cookie
        response = make_response(redirect(url_for('index')))
        response.set_cookie("session_token", session_token, httponly=True, samesite='Strict')

        return response



@app.route("/logout")
def logout():
    response = make_response(redirect(url_for('index')))
    response.set_cookie("intentos", expires=0)
    response.set_cookie("session_token", expires=0)

    return response

@app.route("/profile")
def profile():

    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()

    if user:
        return render_template("profile.html", user=user)
    else:
        return redirect(url_for("index"))


@app.route("/edit_profile", methods=["POST", "GET"])

def edit_profile():

        session_token = request.cookies.get("session_token")

        # get user from the database based on her/his email address
        user = db.query(User).filter_by(session_token=session_token, deleted=False).first()

        if request.method == "GET":

            if user:  # if user is found

                return render_template("edit_profile.html", user=user)

            else:

                return redirect(url_for("index"))

        elif request.method == "POST":
            name = request.form.get("profile-name")
            email = request.form.get("profile-email")
            residencia = request.form.get("profile-residencia")
            old_password = request.form.get("old-password")
            new_password = request.form.get("new-password")

            if old_password and new_password:
                hashed_old_password = hashlib.sha256(old_password.encode()).hexdigest()  # hash de la antigua contraseña
                hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()  # hash de la nueva

                # comparamos
                if hashed_old_password == user.password:
                    # si es correcto, salvamos en BBDD
                    user.password = hashed_new_password
                else:
                    # sino, devolvemos error
                    return "Te has equivocado con tu antigua contraseña socio"

            # actualizamos usuario (nombre y email) en BBDD
            user.name = name
            user.email = email
            user.residencia = residencia

            # guardamos en BBDD
            db.add(user)
            db.commit()

            return redirect(url_for("profile"))


@app.route("/delete_profile", methods=["GET", "POST"])
def delete_profile():
    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token, deleted=False).first()

    if request.method == "GET":
        if user:
            return render_template("delete_profile.html", user=user)
        else:
            return redirect(url_for("index"))
    elif request.method == "POST":
        # fake delete
        user.deleted = True
        db.add(user)
        db.commit()

    response = make_response(redirect(url_for('index')))
    response.set_cookie("session_token", expires=0)

    return response

@app.route("/usuarios")

def usuarios():

    users = db.query(User).filter_by(deleted=False).all() #todos los usuarios activos y q hayan jugado (intentos>0)
    new_score_list = sorted(users, key=lambda k: k.intentos)
    return render_template("usuarios.html", users=new_score_list)

@app.route("/usuario/<user_id>")

def user_details(user_id):
    user = db.query(User).get(int(user_id))

    return render_template("user_details.html", user=user)



@app.route("/mandar", methods=["GET", "POST"])

def mandar():

    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token, deleted=False).first()

    if request.method == "GET":

        if user:

            id = user.id
            users = db.query(User).filter(User.id != id, User.deleted < 1).all()

            return render_template("cojones.html", user=user, users=users)

        else:

            return redirect(url_for("index"))

    elif request.method == "POST":

        asunto = request.form.get("asunto")
        texto = request.form.get("texto")
        para =  request.form.get("para")
        leido = 0
        mensaje = Mensaje(asunto=asunto, texto=texto, leido=leido, destinatario=para, sender=user.email)

        # guardamos el mensaje en la BBDD
        db.add(mensaje)
        db.commit()

        response = make_response(redirect(url_for('index')))

        return response


@app.route("/mensajes")
def mensajes():

    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token, deleted=False).first()

    if request.method == "GET":

        if user:

            mensajes = db.query(Mensaje).filter_by(destinatario=user.email).all()

            return render_template("todos_mensajess.html", user=user, mensajes=mensajes)

        else:

            return redirect(url_for("index"))

@app.route("/mensaje/<mensaje_id>")

def detalles_mensaje(mensaje_id):
    mensaje = db.query(Mensaje).get(int(mensaje_id))

    mensaje.leido = True

    db.add(mensaje)
    db.commit()

    return render_template("mensaje.html", mensaje=mensaje)




if __name__ == '__main__':
    app.run()