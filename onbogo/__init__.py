import pymongo
from apscheduler.schedulers.background import BackgroundScheduler

import os
import logging
import config
import atexit

from flask import Flask

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.
env_short = os.getenv("ENV")

cfg = config
if env_short == "dev":
    cfg = config.DevelopmentConfig
elif env_short == "prod":
    cfg = config.ProductionConfig    
elif env_short == "test":
    cfg = config.TestingConfig    

scheduler = BackgroundScheduler(job_defaults={'max_instances': 2}, daemon=True, logger=logging.getLogger('schedule'))

# database

client = pymongo.MongoClient(os.getenv("DATABASE_URI"))
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

    # activate scheduler
    scheduler.start()
    
    # scheduler time set to UTC
    scheduler.add_job(func=onbogo.run_schedule, trigger='cron', day_of_week='thu', hour=16, minute=00)
    atexit.register(lambda: scheduler.shutdown())

    return app