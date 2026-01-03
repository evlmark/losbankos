"""
Script to run Telegram bot in polling mode
This should be run separately to handle /start commands
Includes HTTP health check server for Render port binding
"""
import os
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from loguru import logger
from telegram_bot import run_bot


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check endpoint for Render"""
    
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Bot is running')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass


def run_health_server():
    """Run HTTP server for Render port binding"""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server started on port {port}")
    try:
        server.serve_forever()
    except Exception as e:
        logger.error(f"Health server error: {e}")


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
    
    # Start health check server in background thread for Render
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Run bot
    run_bot()

