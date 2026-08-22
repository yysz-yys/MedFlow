from apscheduler.schedulers.asyncio import AsyncIOScheduler
from tasks.cleanup import cleanup_task

scheduler = AsyncIOScheduler()


def start_scheduler():
    scheduler.add_job(cleanup_task, "cron", hour=3, minute=0, id="cleanup")
    scheduler.start()
