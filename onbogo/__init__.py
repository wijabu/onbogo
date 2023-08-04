import os
import pymongo
import logging
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

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

    return app



# --------- updated version ---------

# import os
# import pymongo
# import logging
# import atexit
# from apscheduler.schedulers.background import BackgroundScheduler
# from dotenv import load_dotenv

# from flask import Flask
# import config

# from .onbogo import run_schedule

# # logging.basicConfig()
# logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# load_dotenv()  # take environment variables from .env.
# env_short = os.getenv("ENV")

# scheduler = BackgroundScheduler(job_defaults={'max_instances': 2}, daemon=True, logger=logging.getLogger('schedule'))

# cfg = config
# if env_short == "dev":
#     cfg = config.DevelopmentConfig
# elif env_short == "prod":
#     cfg = config.ProductionConfig    
# elif env_short == "test":
#     cfg = config.TestingConfig    

# # database

# # client = pymongo.MongoClient(os.getenv("DATABASE_URI"))
# # db = client.onbogo

# def create_app():
#     app = Flask(__name__)
#     app.config.from_object(cfg)
#     mongo = pymongo(app)
    
#     # UPDATED CHANGES HERE
#     # client = pymongo.MongoClient(os.getenv("DATABASE_URI"))
#     # app.db = client.onbogo
#     # scheduler.init_app(app)
#     logging.debug("onbogo initiating...")

    # with app.app_context():
#         from .auth import auth
#         from .views import views
#         from .errors import errors

#         app.register_blueprint(auth)
#         app.register_blueprint(views)
#         app.register_blueprint(errors)

#     # activate scheduler
#     try:
#         scheduler.start()
#         # scheduler.add_job(func=run_schedule, trigger='cron', day_of_week='thu', hour=12, minute=49)
#         atexit.register(lambda: scheduler.shutdown())
#     except:
#         print("Unable to start scheduler")

#     return app