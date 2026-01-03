"""
Script to run Telegram bot in polling mode
This should be run separately to handle /start commands
"""
from pathlib import Path
from loguru import logger
from telegram_bot import run_bot

if __name__ == "__main__":
    # Create logs directory
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logger
    logger.add(
        logs_dir / "telegram_bot_{time}.log",
        rotation="1 week",
        retention="4 weeks",
        level="INFO"
    )
    
    logger.info("Starting Telegram bot...")
    run_bot()

