-- Supabase Tables Setup Script
-- Generated automatically by setup_supabase.py
-- Execute this in Supabase SQL Editor

-- Create subscribers table
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


-- Create reports table
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


-- Create combined_reports table
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


-- Configure Row Level Security
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

