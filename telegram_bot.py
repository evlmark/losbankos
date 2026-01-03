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
                self._sync_subscribers_to_git(chat_id)
            except Exception as e:
                logger.error(f"Error saving subscriber: {chat_id}: {e}")
    
    def _sync_subscribers_to_git(self, chat_id: int):
        """
        Try to sync subscribers file to git repository
        This ensures GitHub Actions has the latest subscriber list
        """
        try:
            import subprocess
            repo_root = Path(__file__).parent
            
            if not (repo_root / '.git').exists():
                logger.warning("Not a git repository - cannot auto-sync subscribers to GitHub")
                logger.warning("Please manually commit telegram_subscribers.json after subscribing")
                return False
            
            # Check git status
            git_status = subprocess.run(
                ['git', 'status', '--porcelain', str(self.subscribers_file)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if git_status.returncode != 0:
                logger.warning(f"Git status check failed: {git_status.stderr}")
                return False
            
            # Add file
            git_add = subprocess.run(
                ['git', 'add', str(self.subscribers_file)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if git_add.returncode != 0:
                logger.warning(f"Git add failed: {git_add.stderr}")
                return False
            
            # Commit
            git_commit = subprocess.run(
                ['git', 'commit', '-m', f'Auto: Add subscriber {chat_id}'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if git_commit.returncode != 0:
                # Check if there are changes to commit
                if "nothing to commit" in git_commit.stdout.lower():
                    logger.info("Subscriber file already committed")
                    return True
                logger.warning(f"Git commit failed: {git_commit.stderr}")
                return False
            
            logger.info(f"✅ Subscriber file committed to git successfully")
            
            # Try to push (may fail if no credentials, but that's OK)
            try:
                git_push = subprocess.run(
                    ['git', 'push', 'origin', 'main'],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if git_push.returncode == 0:
                    logger.info(f"✅ Subscriber file pushed to GitHub successfully")
                    return True
                else:
                    logger.warning(f"⚠️  Git push failed (this is OK on Render without credentials): {git_push.stderr}")
                    logger.warning(f"⚠️  Please manually push telegram_subscribers.json to GitHub")
                    return False
            except Exception as push_error:
                logger.warning(f"⚠️  Could not push to GitHub (this is OK): {push_error}")
                logger.warning(f"⚠️  Please manually push telegram_subscribers.json to GitHub")
                return False
                
        except Exception as git_error:
            # Git operations are optional, don't fail if they don't work
            logger.warning(f"⚠️  Could not auto-sync subscriber file to git: {git_error}")
            logger.warning(f"⚠️  Please manually commit and push telegram_subscribers.json to GitHub")
            return False
    
    def check_sync_status(self) -> dict:
        """
        Check if subscribers file is synced with git
        Returns status information
        """
        status = {
            'file_exists': False,
            'is_git_repo': False,
            'has_changes': False,
            'is_committed': False,
            'subscriber_count': 0
        }
        
        try:
            # Check if file exists
            if self.subscribers_file.exists():
                status['file_exists'] = True
                subscribers = self.load_subscribers()
                status['subscriber_count'] = len(subscribers)
            
            # Check if git repo
            repo_root = Path(__file__).parent
            if (repo_root / '.git').exists():
                status['is_git_repo'] = True
                
                # Check git status
                import subprocess
                git_status = subprocess.run(
                    ['git', 'status', '--porcelain', str(self.subscribers_file)],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if git_status.returncode == 0:
                    if git_status.stdout.strip():
                        status['has_changes'] = True
                    else:
                        status['is_committed'] = True
                        
        except Exception as e:
            logger.debug(f"Error checking sync status: {e}")
        
        return status
    
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
        """Handle /subscribers command - show subscribers and sync status"""
        subscribers = self.load_subscribers()
        count = len(subscribers)
        
        # Check sync status
        sync_status = self.check_sync_status()
        
        message_parts = []
        
        if count == 0:
            message_parts.append("📭 Список подписчиков пуст.\n\nОтправьте /start чтобы подписаться на отчеты.")
        else:
            message_parts.append(f"👥 Количество подписчиков: {count}")
            message_parts.append(f"Подписчики: {', '.join(map(str, subscribers[:10]))}")
            if count > 10:
                message_parts.append(f"и еще {count - 10}...")
        
        # Add sync status
        message_parts.append("\n🔄 Статус синхронизации:")
        if sync_status['is_git_repo']:
            if sync_status['is_committed']:
                message_parts.append("✅ Файл закоммичен в git")
            elif sync_status['has_changes']:
                message_parts.append("⚠️  Есть незакоммиченные изменения")
                message_parts.append("   Нужно вручную: git add && git commit && git push")
            else:
                message_parts.append("ℹ️  Файл синхронизирован")
        else:
            message_parts.append("⚠️  Не git репозиторий - синхронизация невозможна")
        
        await update.message.reply_text("\n".join(message_parts))
    
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
            
            logger.debug(f"Sending message to {chat_id}, length: {len(message)} chars")
            
            # For reports, use plain text to avoid Markdown parsing errors
            # Reports may contain special characters that break Markdown parsing
            use_parse_mode = None  # Disable parse_mode for reports to avoid parsing errors
            
            if len(message) <= max_length:
                try:
                    # First try with parse_mode
                    result = await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=parse_mode
                    )
                    logger.debug(f"Message sent successfully with {parse_mode}, message_id: {result.message_id}")
                except Exception as parse_error:
                    # If Markdown parsing fails, try without parse_mode
                    if "parse" in str(parse_error).lower() or "entity" in str(parse_error).lower():
                        logger.warning(f"Markdown parsing failed, retrying as plain text: {parse_error}")
                        result = await self.bot.send_message(
                            chat_id=chat_id,
                            text=message,
                            parse_mode=None
                        )
                        logger.debug(f"Message sent successfully as plain text, message_id: {result.message_id}")
                    else:
                        raise
            else:
                # Split message into chunks
                chunks = [message[i:i+max_length] for i in range(0, len(message), max_length)]
                logger.info(f"Message too long ({len(message)} chars), splitting into {len(chunks)} chunks")
                for i, chunk in enumerate(chunks):
                    try:
                        # Try with parse_mode for first chunk only
                        if i == 0:
                            result = await self.bot.send_message(
                                chat_id=chat_id,
                                text=chunk,
                                parse_mode=parse_mode
                            )
                        else:
                            # For subsequent chunks, use plain text to avoid formatting issues
                            result = await self.bot.send_message(
                                chat_id=chat_id,
                                text=chunk,
                                parse_mode=None
                            )
                        logger.debug(f"Chunk {i+1}/{len(chunks)} sent, message_id: {result.message_id}")
                    except Exception as chunk_error:
                        # If parsing fails, retry as plain text
                        if "parse" in str(chunk_error).lower() or "entity" in str(chunk_error).lower():
                            logger.warning(f"Markdown parsing failed for chunk {i+1}, retrying as plain text: {chunk_error}")
                            result = await self.bot.send_message(
                                chat_id=chat_id,
                                text=chunk,
                                parse_mode=None
                            )
                            logger.debug(f"Chunk {i+1}/{len(chunks)} sent as plain text, message_id: {result.message_id}")
                        else:
                            raise
            
            logger.info(f"✅ Message sent to Telegram chat {chat_id} successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending message to Telegram chat {chat_id}: {e}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
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
        logger.info(f"Loading subscribers: found {len(subscribers)} subscribers")
        
        if not subscribers:
            logger.warning("⚠️  No subscribers to send report to")
            logger.warning("⚠️  Make sure users have sent /start to the bot")
            return 0
        
        logger.info(f"📤 Sending report to {len(subscribers)} subscribers...")
        logger.info(f"📊 Report length: {len(report_content)} characters")
        
        success_count = 0
        for chat_id in subscribers:
            try:
                logger.info(f"📨 Attempting to send report to subscriber {chat_id}...")
                result = await self.send_message(chat_id, report_content)
                if result:
                    success_count += 1
                    logger.info(f"✅ Successfully sent report to subscriber {chat_id}")
                else:
                    logger.error(f"❌ Failed to send report to subscriber {chat_id} (send_message returned False)")
            except Exception as e:
                logger.error(f"❌ Error sending to subscriber {chat_id}: {e}")
                logger.error(f"❌ Error type: {type(e).__name__}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        logger.info(f"📊 Report sending complete: {success_count}/{len(subscribers)} successful")
        if success_count == 0:
            logger.error("❌ No reports were sent successfully!")
            logger.error("❌ Check logs above for error details")
        
        return success_count
    
    def run_polling(self):
        """Start bot polling (for interactive mode)"""
        import time
        
        logger.info("Starting Telegram bot polling...")
        
        # Wait longer before starting to let old instance stop (during deployment)
        logger.info("Waiting 30 seconds for any old instances to stop...")
        time.sleep(30)
        
        # Now start polling - run_polling will handle its own event loop
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
                logger.error("Another instance is running. Waiting 60 seconds and retrying...")
                time.sleep(60)
                # Retry once
                try:
                    logger.info("Retrying polling...")
                    self.application.run_polling(
                        allowed_updates=Update.ALL_TYPES,
                        drop_pending_updates=True,
                        close_loop=False
                    )
                except Exception as retry_error:
                    logger.error(f"Bot conflict persists after retry: {retry_error}")
                    logger.error("Please ensure only one instance is running.")
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

