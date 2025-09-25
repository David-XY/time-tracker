from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .github_import import import_all

scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.add_job(import_all, "interval", hours=1)
    scheduler.start()
