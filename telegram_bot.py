"""
Telegram bot for sending reports and handling commands
"""
import json
import os
from pathlib import Path
from typing import List, Optional
from loguru import logger

try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    logger.warning("python-telegram-bot not installed. Bot functionality will not work.")
    Update = None
    Bot = None
    Application = None
    CommandHandler = None
    ContextTypes = None

from config import TELEGRAM_BOT_TOKEN, OUTPUT_DIR


class TelegramBot:
    """Telegram bot for sending reports"""
    
    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        
        # Save subscribers in repo root so it persists in GitHub Actions
        self.subscribers_file = Path(__file__).parent / "telegram_subscribers.json"
        self.subscribers_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize bot
        try:
            self.application = Application.builder().token(self.bot_token).build()
            self.bot = self.application.bot
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("subscribers", self.subscribers_command))
            
            # Add error handler
            async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
                """Handle errors"""
                logger.error(f"Exception while handling an update: {context.error}")
                if "Conflict" in str(context.error):
                    logger.warning("Bot conflict - another instance may be running. This is normal during deployment.")
            
            self.application.add_error_handler(error_handler)
            
        except Exception as e:
            logger.error(f"Error initializing Telegram bot: {e}")
            raise
    
    def load_subscribers(self) -> List[int]:
        """Load list of subscriber chat IDs"""
        if not self.subscribers_file.exists():
            return []
        
        try:
            with open(self.subscribers_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('subscribers', [])
        except Exception as e:
            logger.error(f"Error loading subscribers: {e}")
            return []
    
    def save_subscriber(self, chat_id: int):
        """Add a new subscriber"""
        subscribers = self.load_subscribers()
        if chat_id not in subscribers:
            subscribers.append(chat_id)
            try:
                with open(self.subscribers_file, 'w', encoding='utf-8') as f:
                    json.dump({'subscribers': subscribers}, f, indent=2)
                logger.info(f"Added subscriber: {chat_id}")
                # Try to commit to git if in a git repo (for GitHub Actions)
                try:
                    import subprocess
                    repo_root = Path(__file__).parent
                    if (repo_root / '.git').exists():
                        subprocess.run(
                            ['git', 'add', str(self.subscribers_file)],
                            cwd=repo_root,
                            capture_output=True,
                            timeout=5
                        )
                        subprocess.run(
                            ['git', 'commit', '-m', f'Auto: Add subscriber {chat_id}'],
                            cwd=repo_root,
                            capture_output=True,
                            timeout=5
                        )
                        logger.info(f"Subscriber file committed to git")
                except Exception as git_error:
                    # Git operations are optional, don't fail if they don't work
                    logger.debug(f"Could not auto-commit subscriber file: {git_error}")
            except Exception as e:
                logger.error(f"Error saving subscriber: {chat_id}: {e}")
    
    def get_latest_report(self) -> Optional[Path]:
        """Get the latest combined report"""
        report_files = sorted(OUTPUT_DIR.glob("report_all_*.md"), key=os.path.getmtime, reverse=True)
        if report_files:
            return report_files[0]
        return None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        chat_id = update.effective_chat.id
        
        # Add user to subscribers
        self.save_subscriber(chat_id)
        
        # Send welcome message
        welcome_text = (
            "👋 Привет! Я бот для анализа отзывов конкурентов.\n\n"
            "Я буду автоматически отправлять вам новые отчеты каждую неделю.\n\n"
            "Команды:\n"
            "/start - подписаться на отчеты и получить последний отчет\n"
            "/help - показать эту справку\n\n"
            "Загружаю последний отчет..."
        )
        
        await update.message.reply_text(welcome_text)
        
        # Send latest report
        latest_report = self.get_latest_report()
        if latest_report:
            try:
                with open(latest_report, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                
                # Send report (split if too long)
                await self.send_message(chat_id, report_content)
                await update.message.reply_text("✅ Отчет отправлен!")
                
            except Exception as e:
                logger.error(f"Error sending report: {e}")
                await update.message.reply_text(f"❌ Ошибка при отправке отчета: {e}")
        else:
            await update.message.reply_text(
                "📭 Пока нет доступных отчетов. Первый отчет будет создан при следующем запуске анализа."
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "📚 Справка по боту\n\n"
            "Команды:\n"
            "/start - подписаться на отчеты и получить последний отчет\n"
            "/help - показать эту справку\n"
            "/subscribers - показать количество подписчиков (только для администратора)\n\n"
            "Бот автоматически отправляет новые отчеты всем подписанным пользователям."
        )
        await update.message.reply_text(help_text)
    
    async def subscribers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribers command - show subscriber count"""
        subscribers = self.load_subscribers()
        count = len(subscribers)
        
        if count == 0:
            message = "📭 Список подписчиков пуст.\n\nОтправьте /start чтобы подписаться на отчеты."
        else:
            message = f"👥 Количество подписчиков: {count}\n\n"
            message += f"Подписчики: {', '.join(map(str, subscribers[:10]))}"
            if count > 10:
                message += f" и еще {count - 10}..."
        
        await update.message.reply_text(message)
    
    async def send_message(self, chat_id: int, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send message to Telegram chat
        
        Args:
            chat_id: Chat ID
            message: Message text
            parse_mode: Parse mode (Markdown or HTML)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Telegram has a 4096 character limit, so we need to split long messages
            max_length = 4096
            
            if len(message) <= max_length:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode
                )
            else:
                # Split message into chunks
                chunks = [message[i:i+max_length] for i in range(0, len(message), max_length)]
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=chunk,
                            parse_mode=parse_mode
                        )
                    else:
                        # For subsequent chunks, don't use parse_mode to avoid formatting issues
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=chunk
                        )
            
            logger.info(f"Message sent to Telegram chat {chat_id} successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return False
    
    async def send_report_to_all_subscribers(self, report_content: str) -> int:
        """
        Send report to all subscribers
        
        Args:
            report_content: Report content to send
        
        Returns:
            Number of successful sends
        """
        subscribers = self.load_subscribers()
        if not subscribers:
            logger.info("No subscribers to send report to")
            return 0
        
        success_count = 0
        for chat_id in subscribers:
            try:
                if await self.send_message(chat_id, report_content):
                    success_count += 1
            except Exception as e:
                logger.error(f"Error sending to subscriber {chat_id}: {e}")
        
        logger.info(f"Sent report to {success_count}/{len(subscribers)} subscribers")
        return success_count
    
    async def _check_bot_available(self) -> bool:
        """Check if bot can get updates (no conflict)"""
        try:
            # Try to get updates with timeout=0 to check availability
            updates = await self.bot.get_updates(timeout=0, limit=1)
            return True
        except Exception as e:
            if "Conflict" in str(e) or "getUpdates" in str(e):
                return False
            # Other errors - assume available
            return True
    
    def run_polling(self):
        """Start bot polling (for interactive mode)"""
        import time
        import asyncio
        
        logger.info("Starting Telegram bot polling...")
        
        # Wait longer before starting to let old instance stop (during deployment)
        logger.info("Waiting 30 seconds for any old instances to stop...")
        time.sleep(30)
        
        # Check if bot is available before starting
        logger.info("Checking if bot is available (no conflicts)...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        max_availability_checks = 10
        availability_check_delay = 10  # seconds
        
        for check_attempt in range(max_availability_checks):
            try:
                is_available = loop.run_until_complete(self._check_bot_available())
                if is_available:
                    logger.info("Bot is available, starting polling...")
                    break
                else:
                    logger.warning(f"Bot conflict detected (check {check_attempt + 1}/{max_availability_checks}). Waiting {availability_check_delay}s...")
                    logger.warning("Another instance is still running. This is normal during deployment.")
                    time.sleep(availability_check_delay)
                    availability_check_delay += 5
            except Exception as e:
                logger.warning(f"Error checking bot availability: {e}. Will try to start anyway.")
                break
        
        loop.close()
        
        # Now start polling
        try:
            logger.info("Starting polling...")
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,  # Drop pending updates to avoid conflicts
                close_loop=False
            )
        except Exception as e:
            error_str = str(e)
            if "Conflict" in error_str or "getUpdates" in error_str:
                logger.error("Bot conflict detected during polling.")
                logger.error("Another instance is running. Please ensure only one instance is active.")
                logger.error("If deploying to Render, wait a few minutes and try again.")
                # Exit gracefully instead of crashing
                import sys
                sys.exit(1)
            else:
                logger.error(f"Error in polling: {e}")
                raise


def run_bot():
    """Run bot in polling mode"""
    try:
        bot = TelegramBot()
        bot.run_polling()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        raise

