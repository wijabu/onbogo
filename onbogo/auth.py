import os
import logging

from passlib.hash import pbkdf2_sha256
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
auth = Blueprint("auth", __name__)

from .models import User
from . import db, notify


RESET_TOKEN_SALT = "password-reset"
RESET_TOKEN_MAX_AGE = 3600  # 1 hour


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def _generate_reset_token(email):
    return _serializer().dumps(email, salt=RESET_TOKEN_SALT)


def _verify_reset_token(token):
    try:
        return _serializer().loads(token, salt=RESET_TOKEN_SALT, max_age=RESET_TOKEN_MAX_AGE)
    except SignatureExpired:
        return None
    except BadSignature:
        return None


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


@auth.route("/reset", methods=["GET", "POST"])
def reset_request():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = db.users.find_one({"email": email}) if email else None

        if user:
            token = _generate_reset_token(email)
            reset_url = url_for("auth.reset_with_token", token=token, _external=True)
            body = (
                f"Hi {user.get('username', 'there')},\n\n"
                f"Someone requested a password reset for your onbogo account.\n"
                f"Click the link below to set a new password. This link expires in 1 hour:\n\n"
                f"{reset_url}\n\n"
                f"If you didn't request this, you can safely ignore this email.\n"
            )
            try:
                sender_credentials = (os.getenv("SENDER_EMAIL"), os.getenv("SENDER_PASSWORD"))
                notify.send_email(
                    message=body,
                    sender_credentials=sender_credentials,
                    receiver_email=email,
                    subject="onbogo — password reset",
                )
            except Exception as e:
                logging.error(f"Password reset email failed for {email}: {e}", exc_info=True)

        # Same response whether or not the email exists — prevents account enumeration.
        flash("If that email is registered, a reset link has been sent. Check your inbox.", category="success")
        return redirect(url_for("auth.login"))

    return render_template("reset_request.html")


@auth.route("/reset/<token>", methods=["GET", "POST"])
def reset_with_token(token):
    email = _verify_reset_token(token)
    if not email:
        flash("Reset link is invalid or has expired. Please request a new one.", category="danger")
        return redirect(url_for("auth.reset_request"))

    if request.method == "POST":
        password1 = request.form.get("password1", "")
        password2 = request.form.get("password2", "")

        if len(password1) < 8:
            flash("Password must be a minimum of 8 characters", category="danger")
        elif password1 != password2:
            flash("Passwords do not match", category="danger")
        elif User().update_password(email=email, password=password1):
            flash("Password updated. Please log in.", category="success")
            return redirect(url_for("auth.login"))
        else:
            flash("Unable to update password. Please request a new reset link.", category="danger")
            return redirect(url_for("auth.reset_request"))

    return render_template("reset_form.html", token=token)


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