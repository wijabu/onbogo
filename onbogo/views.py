import ast

from functools import wraps
from flask import Blueprint, render_template, session, request, flash, redirect, url_for
views = Blueprint('views', __name__)

from .models import User
from . import onbogo
from . import store

# Decorators

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if("logged_in") in session:
            return f(*args, **kwargs)
        else:
            return render_template("login.html")
        
    return wrap

# Routes

@views.route("/")
def home():
    return render_template("index.html")


@views.route("/sales", methods=["GET", "POST"])
@login_required
def sales():
    my_store = session["user"]["my_store"]

    try:
        if request.method == "POST":
            email = session["user"]["email"]
            favs = session["user"]["favs"]
            item = request.form["item"]

            if len(item) < 1: 
                flash("Must submit a valid item name", category="danger")
            elif item in favs:
                flash("Item already found on shopping list", category="danger")
            else: 
                favs = favs.append(item)
                
                # add item to shopping list
                User().add_item(email=email, item=item)
                flash(f"{item} added to shopping list!", category="success")
    except:
        flash("ERROR: Unable to add item to list.", category="danger")
    
    return render_template("sales.html",my_store=my_store)


@views.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    try:
        if request.method == "POST":
            email = session["user"]["email"]
            notification = request.form["notification"]
            provider = request.form["provider"]
            phone = request.form["phone"]
            zip = request.form["zip"]

            if notification == "text" and (provider == "" or phone == ""):
                flash("Mobile provider and number required for text notifications", category="danger")
            else: 
                # update session data
                session["user"]["notification"] = notification
                session["user"]["provider"] = provider
                session["user"]["phone"] = phone
                session["user"]["zip"] = zip
                session.modified = True

                # update user profile
                User().update_profile(email=email, notification=notification, provider=provider, phone=phone, zip=zip)
                flash("Profile updated!", category="success")
    except:
        flash("ERROR: Unable to update profile.", category="danger")

    return render_template("profile.html")


@views.route("/account", methods=["GET", "POST"])
@login_required
def account():
    try:
        if request.method == "POST":
            username = request.form["username"]
            email = session["user"]["email"]
            password1 = request.form["password1"]
            password2 = request.form["password2"]

            if len(username) < 2: 
                flash("Username must be a minimum of 3 characters", category="danger")
            elif len(password1) < 8:
                flash("Password must be a minimum of 8 characters", category="danger")
            elif password1 != password2:
                flash("Passwords do not match", category="danger")
            else: 
                # add user to database
                User().update_account(email=email, username=username, password=password1)
                flash("Account updated!", category="success")
                return redirect(url_for("views.profile"))
    except:
        flash("ERROR: Unable to update account.", category="danger")

    return render_template("account.html")


@views.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    user = session["user"]
    email = session["user"]["email"]
    id = session["user"]["_id"]

    try:
        if request.method == "GET":
            delete_option = True
            return render_template("account.html", delete_option=delete_option)
        
        if request.method == "POST":
            User().delete_account(id=id)
            session.clear()
            return redirect("/")

    except:
        flash("ERROR: Unable to delete account at this time", category="danger")




@views.route("/remove", methods=["GET", "POST"])
@login_required
def remove_item():
    my_store = session["user"]["my_store"]
    
    try:
        if request.method == "GET":
            return render_template("sales.html")
        
        email = session["user"]["email"]
        selection = request.form.to_dict()
        discard = list(selection.values())[0]
        favs = session["user"]["favs"]
        favs = favs.remove(discard)

        # remove item from shopping list
        User().remove_item(email=email, item=discard)
        flash(f"{discard} removed from list!", category="success")
    
    except: 
        flash("ERROR: Unable to remove item. Item not found on list", category="danger")
        
    return render_template("sales.html", my_store=my_store)


@views.route("/find", methods=["GET", "POST"])
@login_required
def find():
    user = session["user"]
    my_store = session["user"]["my_store"]
    zip = session["user"]["zip"]

    try:
        if request.method == "GET":
            return render_template("sales.html")
        
        if my_store["store_id"]:
            flash("Finding sales... Check your notifications!", category="success")
            onbogo.run(user=user)
        elif zip:
            flash("Select store to find sales", category="danger")
        else: 
            flash("Must add zip code to profile first", category="danger")
    except:
        flash("ERROR: Unable to find sales at this time.", category="danger")
        
    return render_template("sales.html", my_store=my_store)

        

@views.route("/locate", methods=["GET", "POST"])
@login_required
def locate():
    zip = session["user"]["zip"]
    my_store = session["user"]["my_store"]

    try:
        if zip:         
            stores = store.locate(zip)
            flash(f"{len(stores)} stores found near you. Select one below:", category="success")
            return render_template("sales.html", stores=stores, my_store=my_store)

        else: 
            flash("Must add zip code to profile first", category="danger")
    except:
        flash("ERROR: Unable to locate stores by zip code.", category="danger")
    
    return render_template("sales.html", my_store=my_store)


@views.route("/select", methods=["GET", "POST"])
@login_required
def select_store():
    my_store = session["user"]["my_store"]
    
    
    try:
        email = session["user"]["email"]

        # get value from unknown key
        selection = request.form.to_dict()
        store_str = list(selection.values())[0]
        my_store = ast.literal_eval(store_str)

        # update session data
        session["user"]["my_store"] = my_store
        session.modified = True

        # save selected store to database
        User().select_store(email=email, my_store=my_store)
        flash("Store saved!", category="success")
        return render_template("sales.html", my_store=my_store)
    
    except: 
        flash("ERROR: Unable to save store", category="danger")
        
    return render_template("sales.html")
