import os
import pymongo
from dotenv import load_dotenv

from flask import Flask
import config

load_dotenv()  # take environment variables from .env.
env_short = os.getenv("ENV")

cfg = config
if env_short == "dev":
    cfg = config.DevelopmentConfig
elif env_short == "prod":
    cfg = config.ProductionConfig    
elif env_short == "test":
    cfg = config.TestingConfig    

# database

client = pymongo.MongoClient(cfg.DATABASE_URI)
db = client.onbogo

def create_app():
    app = Flask(__name__)
    app.config.from_object(cfg)

    from .auth import auth
    from .views import views
    from .errors import errors

    app.register_blueprint(auth)
    app.register_blueprint(views)
    app.register_blueprint(errors)

    return app