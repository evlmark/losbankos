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

from config import TELEGRAM_BOT_TOKEN, OUTPUT_DIR, REPORTS_DIR, GIT_TOKEN, SUPABASE_URL, SUPABASE_KEY

# Try to import Supabase client
try:
    from supabase_client import SupabaseClient
    SUPABASE_AVAILABLE = True
except (ImportError, ValueError) as e:
    logger.warning(f"Supabase not available: {e}")
    logger.warning("Falling back to file-based storage")
    SUPABASE_AVAILABLE = False
    SupabaseClient = None


class TelegramBot:
    """Telegram bot for sending reports"""
    
    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        
        # Initialize Supabase client if available
        self.supabase = None
        logger.info(f"Checking Supabase availability...")
        logger.info(f"  SUPABASE_AVAILABLE: {SUPABASE_AVAILABLE}")
        logger.info(f"  SUPABASE_URL: {'✅ Set' if SUPABASE_URL else '❌ Not set'}")
        logger.info(f"  SUPABASE_KEY: {'✅ Set' if SUPABASE_KEY else '❌ Not set'}")
        
        if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
            try:
                logger.info("Initializing Supabase client...")
                self.supabase = SupabaseClient()
                logger.info("✅ Using Supabase for data storage")
            except Exception as e:
                logger.warning(f"⚠️  Could not initialize Supabase: {e}")
                logger.warning(f"⚠️  Error type: {type(e).__name__}")
                import traceback
                logger.warning(f"⚠️  Traceback: {traceback.format_exc()}")
                logger.warning("⚠️  Falling back to file-based storage")
                self.supabase = None
        else:
            if not SUPABASE_AVAILABLE:
                logger.warning("⚠️  Supabase library not available")
            if not SUPABASE_URL:
                logger.warning("⚠️  SUPABASE_URL not set in environment variables")
            if not SUPABASE_KEY:
                logger.warning("⚠️  SUPABASE_KEY not set in environment variables")
        
        # Fallback: file-based storage (for backward compatibility)
        if not self.supabase:
            self.subscribers_file = Path(__file__).parent / "telegram_subscribers.json"
            self.subscribers_file.parent.mkdir(parents=True, exist_ok=True)
            logger.info("📁 Using file-based storage (Supabase not available)")
        
        # Try to update reports from repository (for backward compatibility)
        if not self.supabase:
            self._update_reports_from_repo()
        
        # Initialize bot
        try:
            self.application = Application.builder().token(self.bot_token).build()
            self.bot = self.application.bot
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("subscribers", self.subscribers_command))
            self.application.add_handler(CommandHandler("ping", self.ping_command))
            
            # Add handler for all updates (for debugging)
            async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
                """Log all updates for debugging"""
                if update.message:
                    logger.info(f"📥 Received update: message_id={update.message.message_id}, chat_id={update.effective_chat.id}, text={update.message.text}")
                elif update.callback_query:
                    logger.info(f"📥 Received callback_query: {update.callback_query.data}")
                else:
                    logger.info(f"📥 Received update: {type(update)}")
            
            # Add error handler
            async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
                """Handle errors"""
                logger.error(f"❌ Exception while handling an update: {context.error}")
                logger.error(f"❌ Error type: {type(context.error).__name__}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                if "Conflict" in str(context.error):
                    logger.warning("⚠️  Bot conflict - another instance may be running. This is normal during deployment.")
                # Try to send error message to user if possible
                if update and hasattr(update, 'effective_chat'):
                    try:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=f"❌ An error occurred: {context.error}"
                        )
                    except:
                        pass
            
            self.application.add_error_handler(error_handler)
            
            # Log when bot is ready
            logger.info("✅ Telegram bot initialized successfully")
            logger.info(f"✅ Bot token: {self.bot_token[:10]}...{self.bot_token[-5:]}")
            logger.info(f"✅ Using Supabase: {self.supabase is not None}")
            
        except Exception as e:
            logger.error(f"Error initializing Telegram bot: {e}")
            raise
    
    def load_subscribers(self) -> List[int]:
        """Load list of subscriber chat IDs"""
        if self.supabase:
            logger.info("Loading subscribers from Supabase...")
            subscribers = self.supabase.get_subscribers()
            logger.info(f"✅ Loaded {len(subscribers)} subscribers from Supabase: {subscribers}")
            return subscribers
        
        # Fallback to file-based storage
        logger.info("Loading subscribers from file...")
        if not hasattr(self, 'subscribers_file') or not self.subscribers_file.exists():
            logger.warning(f"⚠️  Subscribers file not found: {getattr(self, 'subscribers_file', 'N/A')}")
            return []
        
        try:
            with open(self.subscribers_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                subscribers = data.get('subscribers', [])
                logger.info(f"✅ Loaded {len(subscribers)} subscribers from file: {subscribers}")
                return subscribers
        except Exception as e:
            logger.error(f"Error loading subscribers: {e}")
            return []
    
    def save_subscriber(self, chat_id: int):
        """Add a new subscriber"""
        if self.supabase:
            success = self.supabase.add_subscriber(chat_id)
            if success:
                logger.info(f"✅ Subscriber {chat_id} saved to Supabase")
            else:
                logger.error(f"❌ Failed to save subscriber {chat_id} to Supabase")
            return
        
        # Fallback to file-based storage
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
        Try to sync subscribers file to git repository using GIT_TOKEN
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
            
            # Check if file has changes
            if not git_status.stdout.strip():
                logger.info("Subscriber file has no changes to commit")
                return True
            
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
            
            # Configure git user (required for commit)
            subprocess.run(
                ['git', 'config', 'user.name', 'Telegram Bot'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            subprocess.run(
                ['git', 'config', 'user.email', 'bot@noreply.github.com'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            
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
                else:
                    logger.warning(f"Git commit failed: {git_commit.stderr}")
                    return False
            
            logger.info(f"✅ Subscriber file committed to git successfully")
            
            # Push to GitHub using GIT_TOKEN if available
            if GIT_TOKEN:
                try:
                    # Get remote URL
                    git_remote = subprocess.run(
                        ['git', 'remote', 'get-url', 'origin'],
                        cwd=repo_root,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if git_remote.returncode == 0:
                        remote_url = git_remote.stdout.strip()
                        # Convert HTTPS URL to include token
                        if remote_url.startswith('https://github.com/'):
                            # Extract repo path (e.g., evlmark/losbankos or evlmark/losbankos.git)
                            repo_path = remote_url.replace('https://github.com/', '').rstrip('/')
                            if repo_path.endswith('.git'):
                                repo_path = repo_path[:-4]
                            
                            # Create URL with token
                            token_url = f'https://{GIT_TOKEN}@github.com/{repo_path}.git'
                            
                            logger.info("Pushing to GitHub using GIT_TOKEN...")
                            # Use token URL as remote for this push
                            git_push = subprocess.run(
                                ['git', 'push', token_url, 'main'],
                                cwd=repo_root,
                                capture_output=True,
                                text=True,
                                timeout=15
                            )
                            
                            if git_push.returncode == 0:
                                logger.info(f"✅ Subscriber file pushed to GitHub successfully")
                                return True
                            else:
                                logger.error(f"❌ Git push failed: {git_push.stderr}")
                                return False
                        else:
                            logger.warning(f"⚠️  Remote URL is not HTTPS, cannot use token: {remote_url}")
                    else:
                        logger.warning(f"⚠️  Could not get remote URL: {git_remote.stderr}")
                except Exception as push_error:
                    logger.error(f"❌ Error pushing to GitHub: {push_error}")
                    return False
            else:
                # Try regular push (may work if credentials are already configured)
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
                        logger.warning(f"⚠️  Git push failed (GIT_TOKEN not set): {git_push.stderr}")
                        logger.warning(f"⚠️  Set GIT_TOKEN in Render Environment Variables to enable auto-sync")
                        logger.warning(f"⚠️  Please manually push telegram_subscribers.json to GitHub")
                        return False
                except Exception as push_error:
                    logger.warning(f"⚠️  Could not push to GitHub: {push_error}")
                    logger.warning(f"⚠️  Set GIT_TOKEN in Render Environment Variables to enable auto-sync")
                    return False
                    
        except Exception as e:
            logger.error(f"Error syncing subscribers to git: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
                
        except Exception as git_error:
            # Git operations are optional, don't fail if they don't work
            logger.warning(f"⚠️  Could not auto-sync subscriber file to git: {git_error}")
            logger.warning(f"⚠️  Please manually commit and push telegram_subscribers.json to GitHub")
            return False
    
    def check_sync_status(self) -> dict:
        """
        Check sync status - Supabase or file-based
        Returns status information
        """
        status = {
            'using_supabase': bool(self.supabase),
            'subscriber_count': 0,
            'supabase_configured': bool(SUPABASE_URL and SUPABASE_KEY),
            'file_exists': False,
            'is_git_repo': False,
            'has_changes': False,
            'is_committed': False,
            'git_token_set': bool(GIT_TOKEN)
        }
        
        if self.supabase:
            # Using Supabase
            try:
                status['subscriber_count'] = self.supabase.get_subscriber_count()
            except Exception as e:
                logger.debug(f"Error getting subscriber count from Supabase: {e}")
        else:
            # File-based storage
            try:
                if hasattr(self, 'subscribers_file') and self.subscribers_file.exists():
                    status['file_exists'] = True
                    subscribers = self.load_subscribers()
                    status['subscriber_count'] = len(subscribers)
                
                # Check if git repo
                repo_root = Path(__file__).parent
                if (repo_root / '.git').exists():
                    status['is_git_repo'] = True
                    
                    # Check git status
                    import subprocess
                    if hasattr(self, 'subscribers_file'):
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
    
    def _update_reports_from_repo(self):
        """
        Try to pull latest reports from repository (for Render deployment).
        This ensures bot has access to latest reports even if they were created in GitHub Actions.
        """
        try:
            import subprocess
            repo_root = Path(__file__).parent
            
            if (repo_root / '.git').exists():
                logger.info("Updating reports from repository...")
                git_pull = subprocess.run(
                    ['git', 'pull', 'origin', 'main'],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if git_pull.returncode == 0:
                    logger.info("✅ Reports updated from repository")
                else:
                    logger.warning(f"⚠️  Could not pull reports from repository: {git_pull.stderr}")
            else:
                logger.debug("Not a git repository, skipping git pull")
        except Exception as e:
            logger.debug(f"Could not update reports from repository: {e}")
            # This is OK - reports might already be up to date or git might not be available
    
    def get_latest_report(self) -> Optional[str]:
        """
        Get the latest combined report content.
        Uses Supabase if available, otherwise falls back to file-based storage.
        """
        # Try Supabase first
        if self.supabase:
            report_content = self.supabase.get_latest_combined_report()
            if report_content:
                logger.info("✅ Retrieved latest report from Supabase")
                return report_content
            logger.warning("No reports found in Supabase")
            return None
        
        # Fallback to file-based storage
        latest_file = REPORTS_DIR / "latest_report.md"
        if latest_file.exists():
            logger.info(f"Found latest report: {latest_file}")
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading report file: {e}")
                return None
        
        # Fallback: search for most recent report_all_*.md
        report_files = sorted(REPORTS_DIR.glob("report_all_*.md"), key=os.path.getmtime, reverse=True)
        if report_files:
            logger.info(f"Found report file: {report_files[0]}")
            try:
                with open(report_files[0], 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading report file: {e}")
                return None
        
        logger.warning(f"No reports found in {REPORTS_DIR}")
        return None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            chat_id = update.effective_chat.id
            logger.info(f"🔵 Received /start command from chat_id: {chat_id}")
            logger.info(f"🔵 Update object: {update}")
            logger.info(f"🔵 Message: {update.message}")
            
            # Add user to subscribers
            logger.info(f"🔵 Step 1: Adding user {chat_id} to subscribers...")
            try:
                self.save_subscriber(chat_id)
                logger.info(f"✅ Step 1 complete: User {chat_id} added to subscribers")
            except Exception as e:
                logger.error(f"❌ Step 1 failed: Error adding subscriber: {e}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            # Send welcome message
            welcome_text = (
                "👋 Hello! I'm a bot for analyzing competitor reviews.\n\n"
                "I will automatically send you new reports every week.\n\n"
                "Commands:\n"
                "/start - subscribe to reports and get the latest report\n"
                "/help - show this help\n\n"
                "Loading the latest report..."
            )
            
            logger.info(f"🔵 Step 2: Sending welcome message to {chat_id}...")
            try:
                await update.message.reply_text(welcome_text)
                logger.info(f"✅ Step 2 complete: Welcome message sent to {chat_id}")
            except Exception as e:
                logger.error(f"❌ Step 2 failed: Error sending welcome message: {e}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                raise
            
            # Try to update reports from repository before reading (only for file-based fallback)
            if not self.supabase:
                logger.info("🔵 Step 3: Updating reports from repository...")
                try:
                    self._update_reports_from_repo()
                    logger.info("✅ Step 3 complete: Reports updated from repository")
                except Exception as e:
                    logger.warning(f"⚠️  Step 3 warning: Could not update reports from repo: {e}")
            
            # Send individual reports (1 message = 1 company)
            logger.info(f"🔵 Step 4: Looking for latest reports...")
            logger.info(f"🔵 Using Supabase: {self.supabase is not None}")
            
            if self.supabase:
                logger.info("🔵 Step 4a: Getting reports from Supabase...")
                try:
                    # Get all individual reports from Supabase
                    reports = self.supabase.get_all_latest_reports()
                    logger.info(f"🔵 Step 4a result: Found {len(reports)} individual reports from Supabase")
                    
                    if reports:
                        logger.info(f"✅ Step 4a complete: Found {len(reports)} reports")
                        success_count = 0
                        for idx, report_data in enumerate(reports, 1):
                            app_name = report_data["app_name"]
                            report_content = report_data["report_content"]
                            logger.info(f"🔵 Step 4b.{idx}: Sending report for {app_name} to {chat_id}...")
                            logger.info(f"🔵 Report length: {len(report_content)} characters")
                            try:
                                result = await self.send_message(chat_id, report_content)
                                if result:
                                    success_count += 1
                                    logger.info(f"✅ Step 4b.{idx} complete: Report for {app_name} sent successfully to {chat_id}")
                                else:
                                    logger.error(f"❌ Step 4b.{idx} failed: Failed to send report for {app_name} to {chat_id}")
                            except Exception as e:
                                logger.error(f"❌ Step 4b.{idx} failed: Error sending report for {app_name}: {e}")
                                import traceback
                                logger.error(f"❌ Traceback: {traceback.format_exc()}")
                        
                        if success_count > 0:
                            logger.info(f"🔵 Step 5: Updating last_report_sent_at for {chat_id}...")
                            try:
                                # Update last_report_sent_at in Supabase
                                if self.supabase:
                                    self.supabase.update_subscriber_last_report_sent(chat_id)
                                logger.info(f"✅ Step 5 complete: Updated last_report_sent_at")
                            except Exception as e:
                                logger.warning(f"⚠️  Step 5 warning: Could not update last_report_sent_at: {e}")
                            
                            logger.info(f"🔵 Step 6: Sending completion message...")
                            try:
                                await update.message.reply_text(f"✅ Reports sent! ({success_count} companies)")
                                logger.info(f"✅ Step 6 complete: Completion message sent")
                            except Exception as e:
                                logger.error(f"❌ Step 6 failed: Could not send completion message: {e}")
                        else:
                            logger.error(f"❌ No reports were sent successfully")
                            try:
                                await update.message.reply_text("❌ Error sending reports. Please try again later.")
                            except Exception as e:
                                logger.error(f"❌ Could not send error message: {e}")
                    else:
                        logger.warning(f"⚠️  No reports found in Supabase for {chat_id}")
                        try:
                            await update.message.reply_text(
                                "📭 No reports available yet. The first report will be created on the next analysis run."
                            )
                        except Exception as e:
                            logger.error(f"❌ Could not send 'no reports' message: {e}")
                except Exception as e:
                    logger.error(f"❌ Step 4a failed: Error getting reports from Supabase: {e}")
                    import traceback
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    try:
                        await update.message.reply_text(f"❌ Error loading reports: {e}")
                    except:
                        logger.error("❌ Could not send error message to user")
            else:
                # Fallback: use combined report from file
                report_content = self.get_latest_report()
                if report_content:
                    logger.info(f"Found combined report (length: {len(report_content)} characters)")
                    try:
                        # Send report (split if too long)
                        logger.info(f"Sending report to {chat_id}...")
                        result = await self.send_message(chat_id, report_content)
                        
                        if result:
                            logger.info(f"✅ Report sent successfully to {chat_id}")
                            await update.message.reply_text("✅ Report sent!")
                        else:
                            logger.error(f"❌ Failed to send report to {chat_id} (send_message returned False)")
                            await update.message.reply_text("❌ Error sending report. Please try again later.")
                        
                    except Exception as e:
                        logger.error(f"❌ Error sending report: {e}")
                        logger.error(f"❌ Error type: {type(e).__name__}")
                        import traceback
                        logger.error(f"❌ Traceback: {traceback.format_exc()}")
                        await update.message.reply_text(f"❌ Error sending report: {e}")
                else:
                    logger.warning(f"No reports found for {chat_id}")
                    await update.message.reply_text(
                        "📭 No reports available yet. The first report will be created on the next analysis run."
                    )
        except Exception as e:
            logger.error(f"❌ Error in start_command: {e}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            try:
                await update.message.reply_text(f"❌ An error occurred: {e}")
            except:
                logger.error("❌ Could not send error message to user")
    
    async def ping_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ping command - simple test to check if bot is working"""
        try:
            chat_id = update.effective_chat.id
            logger.info(f"🏓 Received /ping command from chat_id: {chat_id}")
            await update.message.reply_text("🏓 Pong! Bot is working!")
            logger.info(f"✅ Ping response sent to {chat_id}")
        except Exception as e:
            logger.error(f"❌ Error in ping_command: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "📚 Bot Help\n\n"
            "Commands:\n"
            "/start - subscribe to reports and get the latest report\n"
            "/help - show this help\n"
            "/ping - check if bot is working\n"
            "/subscribers - show subscriber count (admin only)\n\n"
            "The bot automatically sends new reports to all subscribed users."
        )
        await update.message.reply_text(help_text)
    
    async def subscribers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribers command - show subscribers and sync status"""
        subscribers = self.load_subscribers()
        
        # Check if user is admin (you can customize this logic)
        # For now, allow anyone to see subscribers count
        count = len(subscribers)
        
        # Check sync status
        sync_status = self.check_sync_status()
        
        message_parts = []
        
        if count == 0:
            message_parts.append("📭 Subscriber list is empty.\n\nSend /start to subscribe to reports.")
        else:
            message_parts.append(f"👥 Subscriber count: {count}")
            message_parts.append(f"Subscribers: {', '.join(map(str, subscribers[:10]))}")
            if count > 10:
                message_parts.append(f"and {count - 10} more...")
        
        # Add sync status
        message_parts.append("\n🔄 Sync status:")
        
        if sync_status.get('git_token_set', False):
            message_parts.append("✅ GIT_TOKEN configured - automatic sync enabled")
        else:
            message_parts.append("⚠️  GIT_TOKEN not configured - add it to Render Environment Variables")
        
        if sync_status['is_git_repo']:
            if sync_status['is_committed']:
                message_parts.append("✅ File committed to git")
            elif sync_status['has_changes']:
                message_parts.append("⚠️  Uncommitted changes detected")
                message_parts.append("   Manual action needed: git add && git commit && git push")
            else:
                message_parts.append("ℹ️  File synchronized")
        else:
            message_parts.append("⚠️  Not a git repository - sync not possible")
        
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
        failed_chat_ids = []
        for chat_id in subscribers:
            try:
                logger.info(f"📨 Attempting to send report to subscriber {chat_id}...")
                result = await self.send_message(chat_id, report_content)
                if result:
                    success_count += 1
                    logger.info(f"✅ Successfully sent report to subscriber {chat_id}")
                    # Update last_report_sent_at in Supabase
                    if self.supabase:
                        try:
                            self.supabase.update_subscriber_last_report_sent(chat_id)
                        except Exception as e:
                            logger.warning(f"⚠️  Failed to update last_report_sent_at for {chat_id}: {e}")
                else:
                    failed_chat_ids.append(chat_id)
                    logger.error(f"❌ Failed to send report to subscriber {chat_id} (send_message returned False)")
            except Exception as e:
                failed_chat_ids.append(chat_id)
                logger.error(f"❌ Error sending to subscriber {chat_id}: {e}")
                logger.error(f"❌ Error type: {type(e).__name__}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        logger.info(f"📊 Report sending complete: {success_count}/{len(subscribers)} successful")
        if success_count == 0:
            logger.error("❌ No reports were sent successfully!")
            logger.error("❌ Check logs above for error details")
        elif failed_chat_ids:
            logger.warning(f"⚠️  Failed to send to {len(failed_chat_ids)} subscribers: {failed_chat_ids}")
        
        return success_count
    
    def run_polling(self):
        """Start bot polling (for interactive mode)"""
        import time
        
        logger.info("🚀 Starting Telegram bot polling...")
        logger.info(f"🚀 Bot token: {self.bot_token[:10]}...{self.bot_token[-5:]}")
        logger.info(f"🚀 Using Supabase: {self.supabase is not None}")
        
        # Test bot connection first
        try:
            logger.info("🔍 Testing bot connection...")
            bot_info = self.bot.get_me()
            logger.info(f"✅ Bot is connected! Username: @{bot_info.username}, ID: {bot_info.id}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Telegram API: {e}")
            logger.error("❌ Check your TELEGRAM_BOT_TOKEN")
            raise
        
        # Wait longer before starting to let old instance stop (during deployment)
        logger.info("⏳ Waiting 30 seconds for any old instances to stop...")
        time.sleep(30)
        
        # Now start polling - run_polling will handle its own event loop
        try:
            logger.info("🔄 Starting polling...")
            logger.info("🔄 Bot is now listening for updates...")
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
        logger.info("=" * 50)
        logger.info("🤖 Initializing Telegram Bot...")
        logger.info("=" * 50)
        bot = TelegramBot()
        logger.info("=" * 50)
        logger.info("🚀 Starting bot polling...")
        logger.info("=" * 50)
        bot.run_polling()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running bot: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise

