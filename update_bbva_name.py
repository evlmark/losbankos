"""
Script to update BBVA GEMA to BBVA in Supabase
"""
import os
import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Configure logger
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

# Load environment variables
load_dotenv()

# Supabase credentials from .env
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")

def update_bbva_name_via_postgresql(db_url: str) -> bool:
    """Update BBVA GEMA to BBVA using direct PostgreSQL connection"""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        logger.info("🔌 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("✅ Connected to database")
        
        # Update reports table
        logger.info("📝 Updating reports table: BBVA GEMA → BBVA...")
        cursor.execute("UPDATE reports SET app_name = 'BBVA' WHERE app_name = 'BBVA GEMA'")
        rows_updated = cursor.rowcount
        logger.info(f"✅ Updated {rows_updated} reports")
        
        # Update combined_reports table (replace in content)
        logger.info("📝 Updating combined_reports table: replacing BBVA GEMA in content...")
        cursor.execute("UPDATE combined_reports SET report_content = REPLACE(report_content, '📱 BBVA GEMA', '📱 BBVA') WHERE report_content LIKE '%BBVA GEMA%'")
        rows_updated_combined = cursor.rowcount
        logger.info(f"✅ Updated {rows_updated_combined} combined reports")
        
        cursor.close()
        conn.close()
        
        logger.info("✅ Update completed successfully!")
        return True
        
    except ImportError:
        logger.error("❌ psycopg2-binary not installed")
        logger.info("💡 Install it: pip install psycopg2-binary")
        return False
    except Exception as e:
        logger.error(f"❌ Error connecting to database: {e}")
        logger.info("💡 Make sure SUPABASE_DB_URL is correct")
        logger.info("💡 Format: postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres")
        return False

def update_bbva_name():
    """Update BBVA GEMA to BBVA in Supabase"""
    
    logger.info("🚀 Starting BBVA name update...")
    logger.info("")
    
    # Try direct PostgreSQL connection first
    if SUPABASE_DB_URL:
        logger.info("Attempting update via direct PostgreSQL connection...")
        if update_bbva_name_via_postgresql(SUPABASE_DB_URL):
            return True
        else:
            logger.warning("⚠️  Direct PostgreSQL update failed.")
    else:
        logger.warning("⚠️  SUPABASE_DB_URL not set.")
    
    # Fallback: instructions
    logger.info("")
    logger.info("💡 Alternative: Update manually in Supabase Dashboard")
    logger.info("   1. Go to Supabase Dashboard → SQL Editor")
    logger.info("   2. Run this SQL:")
    logger.info("")
    logger.info("   UPDATE reports SET app_name = 'BBVA' WHERE app_name = 'BBVA GEMA';")
    logger.info("   UPDATE combined_reports SET report_content = REPLACE(report_content, '📱 BBVA GEMA', '📱 BBVA') WHERE report_content LIKE '%BBVA GEMA%';")
    logger.info("")
    
    return False

if __name__ == "__main__":
    logger.info("")
    if update_bbva_name():
        logger.info("")
        logger.info("✅ BBVA name update completed successfully!")
    else:
        logger.error("")
        logger.error("❌ Update failed. Please check the errors above or use manual method.")

