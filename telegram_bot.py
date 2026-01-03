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
            "/help - показать эту справку\n\n"
            "Бот автоматически отправляет новые отчеты всем подписанным пользователям."
        )
        await update.message.reply_text(help_text)
    
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
    
    def run_polling(self):
        """Start bot polling (for interactive mode)"""
        logger.info("Starting Telegram bot polling...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def run_bot():
    """Run bot in polling mode"""
    try:
        bot = TelegramBot()
        bot.run_polling()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        raise

