import time
from tasks.scheduler import start_scheduler

if __name__ == "__main__":
    scheduler = start_scheduler()
    print("Приложение запущенно...")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
