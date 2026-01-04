"""
Script to add UPDATE policy for combined_reports table in Supabase
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
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")

def add_update_policy_via_postgresql(db_url: str) -> bool:
    """Add UPDATE policy using direct PostgreSQL connection"""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        logger.info("🔌 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("✅ Connected to database")
        
        # SQL to add UPDATE policy
        sql = """
        DROP POLICY IF EXISTS "Allow update on combined_reports" ON combined_reports;
        CREATE POLICY "Allow update on combined_reports" ON combined_reports
            FOR UPDATE USING (true) WITH CHECK (true);
        """
        
        logger.info("📝 Adding UPDATE policy for combined_reports...")
        cursor.execute(sql)
        logger.info("✅ UPDATE policy added successfully!")
        
        cursor.close()
        conn.close()
        
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

def add_update_policy_via_supabase_api() -> bool:
    """Try to add UPDATE policy via Supabase REST API using rpc"""
    try:
        from supabase import create_client
        from config import SUPABASE_URL, SUPABASE_KEY
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.error("❌ SUPABASE_URL and SUPABASE_KEY must be set")
            return False
        
        logger.info("🔌 Connecting to Supabase...")
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Try to execute SQL via rpc (if function exists) or direct query
        # Note: Supabase doesn't allow arbitrary SQL via REST API for security
        # We need to use PostgreSQL connection or create a function first
        
        logger.warning("⚠️  Supabase REST API doesn't support direct SQL execution")
        logger.warning("⚠️  Need SUPABASE_DB_URL for direct PostgreSQL connection")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

def add_update_policy():
    """Add UPDATE policy for combined_reports table"""
    
    logger.info("🚀 Starting UPDATE policy setup for combined_reports...")
    logger.info("")
    
    # Try direct PostgreSQL connection first
    if SUPABASE_DB_URL:
        logger.info("Attempting setup via direct PostgreSQL connection...")
        if add_update_policy_via_postgresql(SUPABASE_DB_URL):
            return True
        else:
            logger.warning("⚠️  Direct PostgreSQL setup failed.")
    else:
        logger.warning("⚠️  SUPABASE_DB_URL not set.")
    
    # Fallback: instructions
    logger.info("")
    logger.info("💡 Alternative: Add policy manually in Supabase Dashboard")
    logger.info("   1. Go to Supabase Dashboard → SQL Editor")
    logger.info("   2. Run this SQL:")
    logger.info("")
    logger.info("   DROP POLICY IF EXISTS \"Allow update on combined_reports\" ON combined_reports;")
    logger.info("   CREATE POLICY \"Allow update on combined_reports\" ON combined_reports")
    logger.info("       FOR UPDATE USING (true) WITH CHECK (true);")
    logger.info("")
    
    return False

if __name__ == "__main__":
    logger.info("")
    if add_update_policy():
        logger.info("")
        logger.info("✅ UPDATE policy setup completed successfully!")
    else:
        logger.error("")
        logger.error("❌ Setup failed. Please check the errors above or use manual method.")

