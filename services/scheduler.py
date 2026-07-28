"""
Scheduler - Daily updates at 6 PM + manual updates
"""
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from services.data_fetcher import DataFetcher


class UpdateScheduler:
    """Schedule automatic updates"""
    
    def __init__(self, proxy: str = None):
        self.proxy = proxy
        self.scheduler = AsyncIOScheduler()
        self.fetcher = None
    
    def _get_fetcher(self):
        if not self.fetcher:
            self.fetcher = DataFetcher(proxy=self.proxy)
        return self.fetcher
    
    async def daily_job(self):
        """Daily update job at 6 PM"""
        logger.info("Running daily update job...")
        try:
            fetcher = self._get_fetcher()
            result = await fetcher.daily_update()
            logger.info(f"Daily update completed: {result}")
        except Exception as e:
            logger.error(f"Daily update failed: {e}")
    
    async def full_job(self):
        """Full update job"""
        logger.info("Running full update job...")
        try:
            fetcher = self._get_fetcher()
            result = await fetcher.full_update()
            logger.info(f"Full update completed: {result}")
        except Exception as e:
            logger.error(f"Full update failed: {e}")
    
    def start(self):
        """Start scheduler"""
        # Daily update at 6 PM (18:00)
        self.scheduler.add_job(
            self.daily_job,
            CronTrigger(hour=18, minute=0),
            id="daily_update",
            name="Daily Update at 6 PM",
            replace_existing=True
        )
        
        # Full update once a week (Saturday at 2 AM)
        self.scheduler.add_job(
            self.full_job,
            CronTrigger(day_of_week="sat", hour=2, minute=0),
            id="weekly_full",
            name="Weekly Full Update",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Scheduler started - Daily at 6 PM, Weekly full on Saturday 2 AM")
    
    def stop(self):
        """Stop scheduler"""
        self.scheduler.shutdown()
        if self.fetcher:
            self.fetcher.close()
        logger.info("Scheduler stopped")
    
    def get_next_runs(self):
        """Get next scheduled runs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None
            })
        return jobs
