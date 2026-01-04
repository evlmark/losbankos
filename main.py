"""
Main script for Reviews Analyzer service
"""
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

from config import COMPETITORS, OUTPUT_DIR, REVIEWS_PER_APP, TELEGRAM_BOT_TOKEN
from store_scrapers import scrape_all_competitors
from report_generator import ReportGenerator
from review_analyzer import ReviewAnalyzer


def load_competitors_config(config_path: Path) -> list:
    """Load competitors configuration from JSON file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('competitors', [])
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {e}")
        return []


def run_analysis():
    """Main function to run the analysis pipeline"""
    logger.info("Starting reviews analysis pipeline")
    
    # Load competitors configuration
    config_path = Path(__file__).parent / "competitors.json"
    competitors = load_competitors_config(config_path)
    
    if not competitors:
        logger.error("No competitors configured. Please create competitors.json file.")
        return
    
    logger.info(f"Found {len(competitors)} competitors to analyze")
    
    # Step 1: Scrape reviews
    logger.info("Step 1: Scraping reviews from stores...")
    review_files = scrape_all_competitors(competitors, reviews_per_app=REVIEWS_PER_APP)
    
    if not review_files:
        logger.error("No reviews were scraped. Exiting.")
        return
    
    logger.info(f"Scraped reviews from {len(review_files)} sources")
    
    # Step 2: Group reviews by app and store
    logger.info("Step 2: Processing reviews...")
    reviews_by_app = {}
    
    for review_file in review_files:
        try:
            with open(review_file, 'r', encoding='utf-8') as f:
                review_data = json.load(f)
            
            app_name = review_data.get('app_name', 'Unknown')
            store_type = review_data.get('store_type', 'unknown')
            reviews = review_data.get('reviews', [])
            
            if app_name not in reviews_by_app:
                reviews_by_app[app_name] = {}
            
            reviews_by_app[app_name][store_type] = reviews
            
        except Exception as e:
            logger.error(f"Error processing {review_file}: {e}")
            continue
    
    if not reviews_by_app:
        logger.error("No reviews were processed. Exiting.")
        return
    
    # Step 3: Generate reports
    logger.info("Step 3: Generating reports...")
    
    # Initialize LLM analyzer if available
    llm_analyzer = None
    try:
        # Check if API key is set
        from config import OPENAI_API_KEY, LLM_PROVIDER, LLM_MODEL
        if LLM_PROVIDER == "openai":
            if not OPENAI_API_KEY:
                logger.error("❌ OPENAI_API_KEY is not set in environment variables!")
                logger.error("❌ Please set OPENAI_API_KEY in GitHub Secrets")
                logger.error("❌ Translation and LLM summaries will not work without API key")
            else:
                logger.info(f"✅ OPENAI_API_KEY is set (length: {len(OPENAI_API_KEY)} chars)")
                logger.info(f"✅ LLM_PROVIDER: {LLM_PROVIDER}, LLM_MODEL: {LLM_MODEL}")
        
        llm_analyzer = ReviewAnalyzer()
        logger.info("✅ LLM analyzer initialized successfully")
    except ValueError as e:
        logger.error(f"❌ Could not initialize LLM analyzer: {e}")
        logger.error("❌ This usually means API key is missing or invalid")
        logger.error("❌ Reports will be generated without LLM summaries and translations")
    except Exception as e:
        logger.error(f"❌ Could not initialize LLM analyzer: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        logger.error("❌ Reports will be generated without LLM summaries and translations")
    
    report_generator = ReportGenerator(llm_analyzer=llm_analyzer)
    all_reports = []
    
    for app_name, reviews_by_store in reviews_by_app.items():
        logger.info(f"Generating report for {app_name}...")
        report = report_generator.generate_report(app_name, reviews_by_store, use_llm=True, llm_analyzer=llm_analyzer)
        all_reports.append((app_name, report))
        
        # Save individual report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_app_name = app_name.replace(' ', '_').replace('/', '_')
        report_file = OUTPUT_DIR / f"report_{safe_app_name}_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Report saved to {report_file}")
    
    # Combine all reports (for file saving)
    summary_report = "\n\n".join([report for _, report in all_reports])
    
    # Save combined report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    combined_report_file = OUTPUT_DIR / f"report_all_{timestamp}.md"
    with open(combined_report_file, 'w', encoding='utf-8') as f:
        f.write(summary_report)
    
    logger.info(f"Combined report saved to {combined_report_file}")
    
    # Step 4: Send notification via Telegram bot
    logger.info("Step 4: Sending reports to Telegram subscribers...")
    try:
        if not TELEGRAM_BOT_TOKEN:
            logger.error("❌ TELEGRAM_BOT_TOKEN is not set!")
            logger.error("❌ Please set TELEGRAM_BOT_TOKEN in GitHub Secrets")
            logger.warning("Skipping Telegram notifications.")
        else:
            logger.info(f"✅ TELEGRAM_BOT_TOKEN is set (length: {len(TELEGRAM_BOT_TOKEN)} chars)")
            from telegram_bot import TelegramBot
            import asyncio
            
            logger.info("Initializing TelegramBot...")
            bot = TelegramBot()
            logger.info("TelegramBot initialized successfully")
            
            # Send individual reports (1 message = 1 company)
            logger.info("Creating event loop...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("Event loop created, sending reports...")
            
            total_sent = 0
            for app_name, report in all_reports:
                logger.info(f"Sending report for {app_name}...")
                sent_count = loop.run_until_complete(bot.send_report_to_all_subscribers(report))
                total_sent += sent_count
                logger.info(f"Report for {app_name} sent to {sent_count} subscribers")
            
            logger.info("Closing event loop...")
            loop.close()
            logger.info(f"📊 All reports sent: {total_sent} total messages sent to Telegram subscribers")
            
            if total_sent == 0:
                logger.error("❌ No reports were sent! Check logs above for details.")
    except Exception as e:
        logger.error(f"❌ Error sending reports to Telegram: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
    
    logger.info("Analysis pipeline completed")


if __name__ == "__main__":
    # Create logs directory
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logger
    logger.add(
        logs_dir / "reviews_analyzer_{time}.log",
        rotation="1 week",
        retention="4 weeks",
        level="INFO"
    )
    
    run_analysis()

