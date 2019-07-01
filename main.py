import hashlib
import random
import uuid
import datetime

from flask import Flask, render_template, request, make_response, redirect, url_for
from models import User, db

app = Flask(__name__)
db.create_all()  # create (new) tables in the database


@app.route("/", methods=["GET"])
def index():
    session_token = request.cookies.get("session_token")

    if session_token:
        user = db.query(User).filter_by(session_token=session_token).first()
    else:
        user = None

    return render_template("index.html", user=user)


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("user-name")
    email = request.form.get("user-email")
    password = request.form.get("user-password")

    # hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # create a secret number
    secret_number = random.randint(1, 30)
    intentos = '0'

    # see if user already exists
    user = db.query(User).filter_by(email=email).first()

    if not user:
        # create a User object
        user = User(name=name, email=email, secret_number=secret_number, password=hashed_password, intentos=intentos)

        # save the user object into a database
        db.add(user)
        db.commit()

    if user and user.deleted == 1:
        # create a User object
        return "Te diste de baja amigo, date de alta con otro usaurio / Contraseña"


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
        response.set_cookie("intentos", str(intentos))

        return response


@app.route("/result", methods=["POST"])
def result():

    guess = int(request.form.get("guess"))
    session_token = request.cookies.get("session_token")
    intentos = request.cookies.get("intentos")

    # sacamos el usuario por su token de sesión
    user = db.query(User).filter_by(session_token=session_token).first()

    if guess == user.secret_number:
        message = "Enhorabuena {1} ! Efectivamente el número secreto es {0} ".format(str(guess), user.name)


        # create a new random secret number


        #guardamos los intentos
        new_intentos = int(intentos) + 1
        palmares = "Acertaste en {0} intentos".format(str(new_intentos))
        fecha = datetime.date.today()
        hoy = fecha.strftime('%d-%b-%Y')
        new_secret = random.randint(1, 30)
        user.secret_number = new_secret
        user.fecha = hoy

        # si el usuario mejor su resultado o es su primer intento guardamos los intentos
        if user.intentos > new_intentos or user.intentos==0:

            user.intentos = new_intentos

        db.add(user)
        db.commit()
        intentos_cero = 0

        response = make_response(render_template("result.html", message=message, palmares=palmares))
        response.set_cookie("intentos", str(intentos_cero))

        return response


    elif guess > user.secret_number:
        message = "No es correcto, prueba algo menor"
        intentos = request.cookies.get("intentos")
        new_intentos = int(intentos) + 1  # añadimos un intento
        response = make_response(render_template("result.html", message=message, new_intentos=new_intentos))
        response.set_cookie("intentos", str(new_intentos))  # actualizamos cookie de intentos

        response = make_response(render_template("result.html", message=message, new_intentos=new_intentos))
        response.set_cookie("intentos", str(new_intentos))  # actualizamos cookie de intentos

        return response

    elif guess < user.secret_number:
        message = "No es correcto, prueba algo mayor"
        intentos = request.cookies.get("intentos")
        new_intentos = int(intentos) + 1  # añadimos un intento

        response = make_response(render_template("result.html", message=message, new_intentos=new_intentos))
        response.set_cookie("intentos", str(new_intentos))  # actualizamos cookie de intentos

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

if __name__ == '__main__':
    app.run()