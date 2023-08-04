import atexit
from apscheduler.schedulers.background import BackgroundScheduler

from onbogo import onbogo, create_app, cfg

scheduler = BackgroundScheduler(job_defaults={'max_instances': 2}, daemon=True)
app = create_app()


if __name__ == "__main__":
    # activate scheduler
    scheduler.start()
    scheduler.add_job(func=onbogo.run_schedule, trigger='cron', day_of_week='thu', hour=12, minute=30)
    atexit.register(lambda: scheduler.shutdown())

    # Starts the app
    app.run(host=cfg.HOST, port=cfg.PORT, use_reloader=False)