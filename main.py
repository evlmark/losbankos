"""
Main script for Reviews Analyzer service
"""
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

from config import COMPETITORS, OUTPUT_DIR, REPORTS_DIR, REVIEWS_PER_APP, TELEGRAM_BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY
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
    
    # Initialize Supabase client if available
    supabase_client = None
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase_client import SupabaseClient
            supabase_client = SupabaseClient()
            logger.info("✅ Supabase client initialized for saving reports")
        except Exception as e:
            logger.warning(f"⚠️  Could not initialize Supabase client: {e}")
            logger.warning("⚠️  Reports will be saved to files only")
    
    # Generate reports and collect statistics
    app_statistics = {}
    for app_name, reviews_by_store in reviews_by_app.items():
        logger.info(f"Generating report for {app_name}...")
        report = report_generator.generate_report(app_name, reviews_by_store, use_llm=True, llm_analyzer=llm_analyzer)
        all_reports.append((app_name, report))
        
        # Calculate statistics for this app
        all_app_reviews = []
        for reviews in reviews_by_store.values():
            all_app_reviews.extend(reviews)
        
        app_stats = report_generator.calculate_statistics(all_app_reviews, "all")
        app_statistics[app_name] = {
            'total_reviews': len(all_app_reviews),
            'positive_count': app_stats.get('positive_count', 0),
            'neutral_count': app_stats.get('neutral_count', 0),
            'negative_count': app_stats.get('negative_count', 0)
        }
        
        # Save individual report to Supabase
        if supabase_client:
            try:
                logger.info(f"Saving report for {app_name} to Supabase...")
                report_id = supabase_client.save_report(
                    app_name=app_name,
                    report_content=report,
                    total_reviews=app_statistics[app_name]['total_reviews'],
                    positive_count=app_statistics[app_name]['positive_count'],
                    neutral_count=app_statistics[app_name]['neutral_count'],
                    negative_count=app_statistics[app_name]['negative_count'],
                    is_latest=True
                )
                if report_id:
                    logger.info(f"✅ Report for {app_name} saved to Supabase (ID: {report_id})")
                else:
                    logger.error(f"❌ Failed to save report for {app_name} to Supabase: save_report returned None")
            except Exception as e:
                logger.error(f"❌ Error saving report for {app_name} to Supabase: {e}")
                logger.error(f"❌ Error type: {type(e).__name__}")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        # Also save to file (for backward compatibility and artifacts)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_app_name = app_name.replace(' ', '_').replace('/', '_')
        report_file = OUTPUT_DIR / f"report_{safe_app_name}_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Report saved to {report_file}")
    
    # Combine all reports
    summary_report = "\n\n".join([report for _, report in all_reports])
    
    # Calculate total statistics for combined report
    total_reviews_all = sum(stats['total_reviews'] for stats in app_statistics.values())
    total_apps = len(app_statistics)
    
    # Save combined report to Supabase
    if supabase_client:
        try:
            logger.info("Saving combined report to Supabase...")
            report_id = supabase_client.save_combined_report(
                report_content=summary_report,
                total_apps=total_apps,
                total_reviews=total_reviews_all,
                is_latest=True
            )
            if report_id:
                logger.info(f"✅ Combined report saved to Supabase (ID: {report_id})")
            else:
                logger.error("❌ Failed to save combined report to Supabase: save_combined_report returned None")
                import traceback
                logger.error(f"❌ Traceback: {traceback.format_exc()}")
        except Exception as e:
            logger.error(f"❌ Error saving combined report to Supabase: {e}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
    else:
        logger.warning("⚠️  Supabase client not available, combined report not saved to Supabase")
    
    # Also save to files (for backward compatibility and artifacts)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save to OUTPUT_DIR (for artifacts)
    combined_report_file = OUTPUT_DIR / f"report_all_{timestamp}.md"
    with open(combined_report_file, 'w', encoding='utf-8') as f:
        f.write(summary_report)
    logger.info(f"Combined report saved to {combined_report_file}")
    
    # Save to REPORTS_DIR (for backward compatibility)
    repo_report_file = REPORTS_DIR / f"report_all_{timestamp}.md"
    with open(repo_report_file, 'w', encoding='utf-8') as f:
        f.write(summary_report)
    logger.info(f"Report saved to repository: {repo_report_file}")
    
    # Also save latest report (for easy access)
    latest_report_file = REPORTS_DIR / "latest_report.md"
    with open(latest_report_file, 'w', encoding='utf-8') as f:
        f.write(summary_report)
    logger.info(f"Latest report saved to: {latest_report_file}")
    
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
            
            # Send combined report to all subscribers (one message with all companies)
            logger.info("Creating event loop...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("Event loop created, sending combined report...")
            
            logger.info(f"Sending combined report to all subscribers...")
            sent_count = loop.run_until_complete(bot.send_report_to_all_subscribers(summary_report))
            logger.info(f"Combined report sent to {sent_count} subscribers")
            
            logger.info("Closing event loop...")
            loop.close()
            logger.info(f"📊 Report sending complete: {sent_count} subscribers received the report")
            
            if sent_count == 0:
                logger.error("❌ No reports were sent! Check logs above for details.")
            elif sent_count < len(bot.load_subscribers()):
                logger.warning(f"⚠️  Only {sent_count}/{len(bot.load_subscribers())} subscribers received the report. Check logs for errors.")
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

