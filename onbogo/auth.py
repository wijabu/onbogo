from passlib.hash import pbkdf2_sha256

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
auth = Blueprint("auth", __name__)

from . import db
from .models import User


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = db.users.find_one({"email": email})
        if user:
            if pbkdf2_sha256.verify(password, user["password"]):
                flash("Login successsful!", category="success")
                User().start_session(user)
                return redirect(url_for("views.sales"))
            else:
                flash("Email or password incorrect.", category="danger")
                return render_template("login.html")
        else:
            flash("No user found with that email.", category="danger")
            return render_template("login.html")   
    else:
        return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        access_code = request.form["access_code"]

        user = db.users.find_one({"email": email})

        if user:
            flash("Email address is already in use. Choose a unique email.", category="danger")
        elif len(username) < 2: 
            flash("Username must be a minimum of 3 characters", category="danger")
        elif len(email) < 4: 
            flash("Email must be a minimum of 5 characters", category="danger")
        elif len(password1) < 8:
            flash("Password must be a minimum of 8 characters", category="danger")
        elif password1 != password2:
            flash("Passwords do not match", category="danger")
        elif access_code != current_app.config['REGISTER_KEY']:
            flash("Authorization code required to create account", category="danger")
            print(access_code)
        else: 
            # add user to database
            User().register(email=email, username=username, password=password1)
            flash("Account created!", category="success")
            return redirect(url_for("views.profile"))

    return render_template("register.html")