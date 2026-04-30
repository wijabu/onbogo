import pymongo
from apscheduler.schedulers.background import BackgroundScheduler

import os
import logging
import config
import atexit

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

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

    # Trust X-Forwarded-* headers from Caddy so url_for(_external=True) builds https:// URLs
    # and request.remote_addr reflects the real client IP.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    from .auth import auth
    from .views import views
    from .errors import errors
    from .extensions import limiter
    from . import onbogo

    limiter.init_app(app)

    app.register_blueprint(auth)
    app.register_blueprint(views)
    app.register_blueprint(errors)

    # activate scheduler
    scheduler.start()

    # Cron is in UTC. 16:30 UTC = 12:30pm EDT / 11:30am EST.
    # misfire_grace_time=3600 means a 1-hour window after the scheduled time is still eligible
    # to run — covers gunicorn restarts during deploys without dropping the alert.
    # coalesce=True collapses any backlog into a single run if multiple are missed.
    scheduler.add_job(
        func=onbogo.run_schedule,
        trigger='cron',
        day_of_week='thu',
        hour=16,
        minute=30,
        misfire_grace_time=3600,
        coalesce=True,
        id='weekly_alerts',
        replace_existing=True,
    )
    atexit.register(lambda: scheduler.shutdown())

    return app