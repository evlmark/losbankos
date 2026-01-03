"""
Scheduler module for running the analysis on a schedule
"""
import schedule
import time
from loguru import logger
from config import SCHEDULE_DAY_OF_WEEK, SCHEDULE_TIME
from main import run_analysis


def setup_scheduler():
    """Setup the weekly scheduler"""
    # Map day names to schedule functions
    day_mapping = {
        'monday': schedule.every().monday,
        'tuesday': schedule.every().tuesday,
        'wednesday': schedule.every().wednesday,
        'thursday': schedule.every().thursday,
        'friday': schedule.every().friday,
        'saturday': schedule.every().saturday,
        'sunday': schedule.every().sunday
    }
    
    day_func = day_mapping.get(SCHEDULE_DAY_OF_WEEK.lower())
    if not day_func:
        logger.error(f"Invalid day of week: {SCHEDULE_DAY_OF_WEEK}")
        return
    
    # Schedule the job
    day_func.at(SCHEDULE_TIME).do(run_analysis)
    
    logger.info(f"Scheduled analysis to run every {SCHEDULE_DAY_OF_WEEK} at {SCHEDULE_TIME}")


def run_scheduler():
    """Run the scheduler loop"""
    setup_scheduler()
    
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    from pathlib import Path
    
    # Create logs directory
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logger
    logger.add(
        logs_dir / "scheduler_{time}.log",
        rotation="1 week",
        retention="4 weeks",
        level="INFO"
    )
    
    run_scheduler()

