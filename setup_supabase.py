"""
Script to automatically set up Supabase tables for reviews analyzer
Run this script after setting up Supabase project and credentials
"""
import os
import sys
from pathlib import Path
from loguru import logger

# Configure logger
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


def setup_supabase_tables():
    """Set up all required tables in Supabase"""
    
    # Check for Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase_db_url = os.getenv("SUPABASE_DB_URL")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        logger.error("❌ Please set them in .env file or export them")
        return False
    
    logger.info("✅ Supabase credentials found")
    logger.info(f"   URL: {supabase_url}")
    logger.info(f"   Key: {supabase_key[:20]}...")
    
    # SQL scripts to execute
    sql_scripts = [
        {
            "name": "Create subscribers table",
            "sql": """
-- Таблица подписчиков Telegram бота
CREATE TABLE IF NOT EXISTS subscribers (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL,
    subscribed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    last_report_sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индекс для быстрого поиска по chat_id
CREATE INDEX IF NOT EXISTS idx_subscribers_chat_id ON subscribers(chat_id);

-- Индекс для активных подписчиков
CREATE INDEX IF NOT EXISTS idx_subscribers_active ON subscribers(is_active) WHERE is_active = TRUE;
"""
        },
        {
            "name": "Create reports table",
            "sql": """
-- Таблица отчетов
CREATE TABLE IF NOT EXISTS reports (
    id BIGSERIAL PRIMARY KEY,
    app_name TEXT NOT NULL,
    report_content TEXT NOT NULL,
    report_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_reviews INTEGER,
    positive_count INTEGER,
    neutral_count INTEGER,
    negative_count INTEGER,
    is_latest BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индекс для поиска последнего отчета
CREATE INDEX IF NOT EXISTS idx_reports_latest ON reports(is_latest) WHERE is_latest = TRUE;

-- Индекс для поиска по дате
CREATE INDEX IF NOT EXISTS idx_reports_date ON reports(report_date DESC);

-- Индекс для поиска по приложению
CREATE INDEX IF NOT EXISTS idx_reports_app_name ON reports(app_name);
"""
        },
        {
            "name": "Create combined_reports table",
            "sql": """
-- Таблица для комбинированных отчетов (все компании вместе)
CREATE TABLE IF NOT EXISTS combined_reports (
    id BIGSERIAL PRIMARY KEY,
    report_content TEXT NOT NULL,
    report_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_apps INTEGER,
    total_reviews INTEGER,
    is_latest BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индекс для последнего комбинированного отчета
CREATE INDEX IF NOT EXISTS idx_combined_reports_latest ON combined_reports(is_latest) WHERE is_latest = TRUE;

-- Индекс для поиска по дате
CREATE INDEX IF NOT EXISTS idx_combined_reports_date ON combined_reports(report_date DESC);
"""
        },
        {
            "name": "Configure Row Level Security",
            "sql": """
-- Включить RLS для таблиц
ALTER TABLE subscribers ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE combined_reports ENABLE ROW LEVEL SECURITY;

-- Политики для subscribers (разрешить все операции через API)
DROP POLICY IF EXISTS "Allow all operations on subscribers" ON subscribers;
CREATE POLICY "Allow all operations on subscribers" ON subscribers
    FOR ALL USING (true) WITH CHECK (true);

-- Политики для reports (разрешить чтение всем, запись через API)
DROP POLICY IF EXISTS "Allow read on reports" ON reports;
CREATE POLICY "Allow read on reports" ON reports
    FOR SELECT USING (true);
    
DROP POLICY IF EXISTS "Allow insert on reports" ON reports;
CREATE POLICY "Allow insert on reports" ON reports
    FOR INSERT WITH CHECK (true);

-- Политики для combined_reports
DROP POLICY IF EXISTS "Allow read on combined_reports" ON combined_reports;
CREATE POLICY "Allow read on combined_reports" ON combined_reports
    FOR SELECT USING (true);
    
DROP POLICY IF EXISTS "Allow insert on combined_reports" ON combined_reports;
CREATE POLICY "Allow insert on combined_reports" ON combined_reports
    FOR INSERT WITH CHECK (true);
"""
        }
    ]
    
    # Try to use Supabase Python client
    try:
        from supabase import create_client, Client
        
        logger.info("📦 Using Supabase Python client...")
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Execute SQL through Supabase REST API (using rpc or direct SQL)
        # Note: Supabase REST API doesn't support arbitrary SQL execution
        # We need to use direct PostgreSQL connection or Supabase SQL Editor
        
        logger.warning("⚠️  Supabase Python client doesn't support arbitrary SQL execution")
        logger.info("📝 Please use one of the following methods:")
        logger.info("   1. Use direct PostgreSQL connection (if SUPABASE_DB_URL is set)")
        logger.info("   2. Copy SQL scripts to Supabase SQL Editor")
        
        if supabase_db_url:
            return setup_via_postgresql(supabase_db_url, sql_scripts)
        else:
            logger.info("💡 Generating SQL file for manual execution...")
            return generate_sql_file(sql_scripts)
            
    except ImportError:
        logger.warning("⚠️  supabase library not installed")
        logger.info("💡 Installing supabase library...")
        logger.info("   Run: pip install supabase psycopg2-binary")
        
        if supabase_db_url:
            return setup_via_postgresql(supabase_db_url, sql_scripts)
        else:
            logger.info("💡 Generating SQL file for manual execution...")
            return generate_sql_file(sql_scripts)


def setup_via_postgresql(db_url: str, sql_scripts: list) -> bool:
    """Set up tables using direct PostgreSQL connection"""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        logger.info("🔌 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("✅ Connected to database")
        
        for script in sql_scripts:
            logger.info(f"📝 Executing: {script['name']}...")
            try:
                cursor.execute(script['sql'])
                logger.info(f"✅ {script['name']} - Success")
            except Exception as e:
                # Some errors are OK (like "already exists")
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    logger.warning(f"⚠️  {script['name']} - Already exists (this is OK)")
                else:
                    logger.error(f"❌ {script['name']} - Error: {e}")
                    return False
        
        cursor.close()
        conn.close()
        
        logger.info("✅ All tables created successfully!")
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


def generate_sql_file(sql_scripts: list) -> bool:
    """Generate SQL file for manual execution in Supabase SQL Editor"""
    sql_file = Path(__file__).parent / "supabase_setup.sql"
    
    logger.info(f"📝 Generating SQL file: {sql_file}")
    
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write("-- Supabase Tables Setup Script\n")
        f.write("-- Generated automatically by setup_supabase.py\n")
        f.write("-- Execute this in Supabase SQL Editor\n\n")
        
        for script in sql_scripts:
            f.write(f"-- {script['name']}\n")
            f.write(script['sql'])
            f.write("\n\n")
    
    logger.info(f"✅ SQL file created: {sql_file}")
    logger.info("📋 Next steps:")
    logger.info("   1. Open Supabase Dashboard → SQL Editor")
    logger.info(f"   2. Copy contents of {sql_file}")
    logger.info("   3. Paste and execute in SQL Editor")
    
    return True


if __name__ == "__main__":
    logger.info("🚀 Starting Supabase tables setup...")
    logger.info("")
    
    # Load environment variables from .env if exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("✅ Loaded .env file")
    except ImportError:
        logger.debug("python-dotenv not installed, skipping .env load")
    except Exception:
        logger.debug("No .env file found")
    
    success = setup_supabase_tables()
    
    if success:
        logger.info("")
        logger.info("✅ Setup completed successfully!")
        logger.info("🎉 You can now use Supabase in your application")
    else:
        logger.error("")
        logger.error("❌ Setup failed. Please check the errors above.")
        sys.exit(1)

