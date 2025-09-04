-- Initialize fraud monitoring database
-- This script sets up the database schema with security best practices

-- Create database user with limited privileges
-- Note: This is handled by Docker environment variables

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create tables with proper constraints and indexes

-- Messages table for storing Telegram messages
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    telegram_message_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    user_id BIGINT,
    username VARCHAR(255),
    message_text TEXT,
    message_type VARCHAR(50) NOT NULL CHECK (message_type IN ('text', 'photo', 'document', 'video', 'caption', 'other')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT unique_message_per_group UNIQUE(telegram_message_id, group_id)
);

-- Images table for storing image metadata and OCR results
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    file_id VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    ocr_text TEXT,
    ocr_confidence FLOAT CHECK (ocr_confidence >= 0 AND ocr_confidence <= 100),
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alerts table for fraud detection alerts
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL,
    keywords_found TEXT[],
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'dismissed', 'escalated')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notified_at TIMESTAMP WITH TIME ZONE,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewer_notes TEXT
);

-- Audit log table for security events
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    user_id BIGINT,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_messages_group_id ON messages(group_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);

CREATE INDEX IF NOT EXISTS idx_images_message_id ON images(message_id);
CREATE INDEX IF NOT EXISTS idx_images_created_at ON images(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_images_confidence ON images(ocr_confidence DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_confidence ON alerts(confidence_score DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);

-- Full-text search indexes for message content
CREATE INDEX IF NOT EXISTS idx_messages_text_search ON messages USING gin(to_tsvector('english', message_text));
CREATE INDEX IF NOT EXISTS idx_images_ocr_search ON images USING gin(to_tsvector('english', ocr_text));

-- Security: Row Level Security (RLS) policies
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE images ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Create policies for application access
-- Note: In production, create specific roles with limited access

-- Views for monitoring and reporting
CREATE OR REPLACE VIEW alert_summary AS
SELECT 
    alert_type,
    status,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence,
    MAX(created_at) as latest_alert
FROM alerts 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY alert_type, status;

CREATE OR REPLACE VIEW daily_message_stats AS
SELECT 
    DATE(created_at) as date,
    message_type,
    COUNT(*) as message_count,
    COUNT(DISTINCT group_id) as unique_groups,
    COUNT(DISTINCT user_id) as unique_users
FROM messages 
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), message_type
ORDER BY date DESC;

-- Functions for data cleanup and maintenance
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Delete old audit logs (keep 90 days)
    DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';
    
    -- Delete old processed images (keep 30 days)
    DELETE FROM images WHERE created_at < NOW() - INTERVAL '30 days' AND processed_at IS NOT NULL;
    
    -- Update old alert statuses
    UPDATE alerts SET status = 'dismissed' 
    WHERE status = 'pending' AND created_at < NOW() - INTERVAL '7 days';
    
    -- Log cleanup action
    INSERT INTO audit_logs (event_type, details) 
    VALUES ('data_cleanup', '{"action": "automated_cleanup"}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled cleanup job (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT cleanup_old_data();');

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fraud_monitor;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fraud_monitor;
GRANT EXECUTE ON FUNCTION cleanup_old_data() TO fraud_monitor;

-- Insert initial configuration data
INSERT INTO audit_logs (event_type, details) 
VALUES (
  'database_initialized',
  jsonb_build_object(
    'version', '1.0',
    'timestamp', NOW()
  ))
ON CONFLICT DO NOTHING;

