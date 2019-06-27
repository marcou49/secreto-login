import hashlib
import random
import uuid

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
        new_secret = random.randint(1, 30)

        #guardamos los intentos
        new_intentos = int(intentos) + 1
        palmares = "Acertaste en {0} intentos".format(str(new_intentos))
        user.intentos = new_intentos

        # update the user's secret number
        user.secret_number = new_secret

        # update the user object in a database
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


if __name__ == '__main__':
    app.run()