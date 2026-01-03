"""
Module for sending notifications to Telegram and Slack
"""
from typing import Optional
from loguru import logger

from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    SLACK_BOT_TOKEN, SLACK_CHANNEL_ID,
    NOTIFICATION_METHOD
)


class TelegramNotifier:
    """Notifier for Telegram"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
        
        try:
            from telegram import Bot
            self.bot = Bot(token=self.bot_token)
        except ImportError:
            raise ImportError("python-telegram-bot is not installed")
    
    def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send message to Telegram channel
        
        Args:
            message: Message text
            parse_mode: Parse mode (Markdown or HTML)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Telegram has a 4096 character limit, so we need to split long messages
            max_length = 4096
            if len(message) <= max_length:
                self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=parse_mode
                )
            else:
                # Split message into chunks
                chunks = [message[i:i+max_length] for i in range(0, len(message), max_length)]
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        self.bot.send_message(
                            chat_id=self.chat_id,
                            text=chunk,
                            parse_mode=parse_mode
                        )
                    else:
                        # For subsequent chunks, don't use parse_mode to avoid formatting issues
                        self.bot.send_message(
                            chat_id=self.chat_id,
                            text=chunk
                        )
            
            logger.info("Message sent to Telegram successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return False


class SlackNotifier:
    """Notifier for Slack"""
    
    def __init__(self, bot_token: Optional[str] = None, channel_id: Optional[str] = None):
        self.bot_token = bot_token or SLACK_BOT_TOKEN
        self.channel_id = channel_id or SLACK_CHANNEL_ID
        
        if not self.bot_token or not self.channel_id:
            raise ValueError("SLACK_BOT_TOKEN and SLACK_CHANNEL_ID must be set")
        
        try:
            from slack_sdk import WebClient
            self.client = WebClient(token=self.bot_token)
        except ImportError:
            raise ImportError("slack-sdk is not installed")
    
    def send_message(self, message: str) -> bool:
        """
        Send message to Slack channel
        
        Args:
            message: Message text
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Format message as code block for better readability
            formatted_message = f"```\n{message}\n```"
            
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=formatted_message
            )
            
            if response["ok"]:
                logger.info("Message sent to Slack successfully")
                return True
            else:
                logger.error(f"Slack API error: {response.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message to Slack: {e}")
            return False


def get_notifier():
    """
    Get the appropriate notifier based on configuration
    
    Returns:
        TelegramNotifier or SlackNotifier instance
    """
    if NOTIFICATION_METHOD == "telegram":
        return TelegramNotifier()
    elif NOTIFICATION_METHOD == "slack":
        return SlackNotifier()
    else:
        raise ValueError(f"Unknown notification method: {NOTIFICATION_METHOD}")

