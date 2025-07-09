-- 🦕🚀 STARCRUNCH DATABASE SCHEMA
-- MySQL database setup for fps.ms hosting

-- Users table - stores Discord user data and preferences
CREATE TABLE IF NOT EXISTS users (
    discord_id VARCHAR(20) PRIMARY KEY,
    preferences JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tasks table - stores all user tasks with scheduling info
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    text TEXT NOT NULL,
    category VARCHAR(20) DEFAULT 'generic',
    priority VARCHAR(10) DEFAULT 'medium',
    completed BOOLEAN DEFAULT FALSE,
    duration INTEGER DEFAULT 60,
    scheduled_time VARCHAR(20),
    scheduled_day VARCHAR(50),
    is_appointment BOOLEAN DEFAULT FALSE,
    ai_enhanced BOOLEAN DEFAULT FALSE,
    adhd_tips JSON,
    scheduling_suggestions JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_completed (completed),
    INDEX idx_scheduled_day (scheduled_day)
);

-- Daily notes table - stores user notes for specific dates
CREATE TABLE IF NOT EXISTS daily_notes (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    date_string VARCHAR(30) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_date (user_id, date_string),
    INDEX idx_user_date (user_id, date_string)
);

-- Learning rules table - stores AI learning patterns
CREATE TABLE IF NOT EXISTS learning_rules (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    rule_type VARCHAR(20) NOT NULL,
    pattern TEXT NOT NULL,
    action TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- Sessions table - for tracking focus/work sessions
CREATE TABLE IF NOT EXISTS focus_sessions (
    id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    session_type VARCHAR(20) NOT NULL, -- 'pomodoro', 'animedoro', 'deep_work'
    duration INTEGER NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_started_at (started_at)
);

-- Create indexes for better performance
CREATE INDEX idx_tasks_user_created ON tasks(user_id, created_at);
CREATE INDEX idx_tasks_user_completed ON tasks(user_id, completed, created_at);
CREATE INDEX idx_notes_user_date ON daily_notes(user_id, date_string);