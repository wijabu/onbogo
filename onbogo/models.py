import uuid
import logging
import time
from passlib.hash import pbkdf2_sha256

from flask import jsonify, session


from . import db


class User():
    def start_session(self, user):
        del user["password"]
        session["logged_in"] = True
        session["user"] = user
        return jsonify(user), 200


    def register(self, username, email, password):

        # create the user object
        user = {
            "_id": uuid.uuid4().hex,
            "username":username,
            "email":email,
            "password":password,
            "sale_id": 5232540,
            "my_store": {
                "title": "",
                "address": "",
                "store_id": ""
            },
            "zip": "",
            "phone": "",
            "provider": "",
            "notification": "text",
            "favs": [],
            "my_sale_items": []
        }

        # encrypt the password
        user["password"] = pbkdf2_sha256.hash(user["password"])

        # Check for unique email address
        if db.users.find_one({"email": email}):
            print ("ERROR 400: Email address is already in use")
            return jsonify({ "error": "Email address is already in use" }), 400

        if db.users.insert_one(user):
            return self.start_session(user)

        return jsonify({"ERROR": "Signup failed"}), 400
    

    def update_account(self, email, username, password):
        # encrypt the password
        password = pbkdf2_sha256.hash(password)
        
        # confirm user found in database
        user = db.users.find_one({"email": email})
        
        if user:
            db.users.update_one(
                {"email": email}, 
                {"$set": 
                    {"username": username,
                    "password": password}
                }, upsert=True)
            print ("Account updated!")
            return jsonify(user), 200
    
    
    def delete_account(self, id):
        # confirm user found in database
        user = db.users.find_one({"_id": id})
        
        if user:
            print(f"Deleting account for user_id: {id}")
            db.users.delete_one(
                {"_id": id})
            
        # return user


    def update_profile(self, email, notification, provider, phone, zip):
        user = db.users.find_one({"email": email})
        
        if user:
            db.users.update_one(
                {"email": email}, 
                {"$set": 
                    {"notification": notification,
                    "provider": provider,
                    "phone": phone,
                    "zip": zip}
                }, upsert=True)
            print ("Profile updated!")
            return jsonify(user), 200
    

    def add_item(self, email, item):
        user = db.users.find_one({"email": email})
        
        if user:
            db.users.update_one(
                {"email": email}, 
                {"$push": 
                    {"favs": item}
                }, upsert=True)
            print (f"{item} added to search list!")
            return jsonify(user), 200
    

    def remove_item(self, email, item):
        user = db.users.find_one({"email": email})
        
        if user:
            db.users.update_one(
                {"email": email}, 
                {"$pull": 
                    {"favs": item}
                }, upsert=True)
            print (f"{item} removed from search list!")
            return jsonify(user), 200
        

    def select_store(self, email, my_store):
        user = db.users.find_one({"email": email})

        if user:
            db.users.update_one(
                {"email": email}, 
                {"$set": 
                    {"my_store": my_store}
                }, upsert=True)
            print ("Profile updated!")
            return jsonify(user), 200
        
        return jsonify("ERROR: unable to update profile with selected store"), 400
    
    
    # def my_sales(self, email, my_sale_items):
    #     user = db.users.find_one({"email": email})
    #     logging.debug(f"my_sale_items value to be set to {user['username']}'s profile: {my_sale_items}")
    #     logging.debug(f"Value found in {user['username']}'s basket BEFORE update: {user['my_sale_items']}")

    #     if user:
    #         db.users.update_one(
    #             {"email": email}, 
    #             {"$set": 
    #                 {"my_sale_items": my_sale_items}
    #             }, upsert=True)
            
    #         # time.sleep(30)
    #         print (f"Updated sale items in {user['username']}'s profile!")
    #         # time.sleep(30)
    #         user = db.users.find_one({"email": email})
    #         logging.debug(f"Value found in {user['username']}'s basket AFTER update: {user['my_sale_items']}")
    #         logging.debug(f"DB updated user: {user}")
            
    #         return user
        
    #     return jsonify("ERROR: unable to add sale items to user profile."), 400