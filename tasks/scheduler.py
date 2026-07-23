from apscheduler.schedulers.background import BackgroundScheduler
from tasks.kufar_jobs import kufar_fetch_job


def start_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        kufar_fetch_job, trigger="interval", minutes=1, max_instances=1
    )

    scheduler.start()
    return scheduler
