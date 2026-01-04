-- Update BBVA GEMA to BBVA in Supabase
-- Execute this in Supabase SQL Editor

-- Update reports table
UPDATE reports 
SET app_name = 'BBVA' 
WHERE app_name = 'BBVA GEMA';

-- Update combined_reports table (if report_content contains "BBVA GEMA")
-- Note: This updates the content, not the app_name field
UPDATE combined_reports 
SET report_content = REPLACE(report_content, '📱 BBVA GEMA', '📱 BBVA')
WHERE report_content LIKE '%BBVA GEMA%';

